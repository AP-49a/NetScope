/**
 * static/js/app.js — NetScope Dashboard Client Controller
 * Asynchronous API client, DOM rendering, and real-time device filtering.
 */

"use strict";

(function () {
  // -------------------------------------------------------------------------
  // Application State
  // -------------------------------------------------------------------------
  const state = {
    network: null,
    devices: [],
    filteredDevices: [],
    isScanning: false,
    status: "idle",
    searchQuery: "",
    statusFilter: "all",
    pollTimer: null,
  };

  // -------------------------------------------------------------------------
  // DOM Elements Cache
  // -------------------------------------------------------------------------
  const els = {
    // Header status
    statusBadge: document.getElementById("status-badge"),
    statusText: document.getElementById("status-text"),

    // Alert Banner
    alertBanner: document.getElementById("alert-banner"),
    alertMessage: document.getElementById("alert-message"),
    alertDismiss: document.getElementById("alert-dismiss"),

    // Network Overview Cards
    adapterName: document.getElementById("adapter-name"),
    adapterType: document.getElementById("adapter-type"),
    localIp: document.getElementById("local-ip"),
    localIpSub: document.getElementById("local-ip-sub"),
    subnetMask: document.getElementById("subnet-mask"),
    subnetPrefix: document.getElementById("subnet-prefix"),
    gatewayIp: document.getElementById("gateway-ip"),

    // Actions & Stats
    scanBtn: document.getElementById("scan-btn"),
    scanSpinner: document.getElementById("scan-spinner"),
    scanBtnText: document.getElementById("scan-btn-text"),
    scanProgressMsg: document.getElementById("scan-progress-msg"),
    statDeviceCount: document.getElementById("stat-device-count"),
    statCidr: document.getElementById("stat-cidr"),
    statDuration: document.getElementById("stat-duration"),

    // Filter & Search Controls
    searchInput: document.getElementById("search-input"),
    searchClear: document.getElementById("search-clear"),
    statusFilter: document.getElementById("status-filter"),

    // Device Table & States
    devicesTable: document.getElementById("devices-table"),
    devicesTbody: document.getElementById("devices-tbody"),
    tableEmpty: document.getElementById("table-empty"),
    tableNoResults: document.getElementById("table-no-results"),
  };

  // -------------------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------------------
  function init() {
    bindEvents();
    loadNetworkConfig();
    checkInitialStatus();
  }

  function bindEvents() {
    els.scanBtn.addEventListener("click", onScanClick);
    els.searchInput.addEventListener("input", onSearchInput);
    els.searchClear.addEventListener("click", onSearchClear);
    els.statusFilter.addEventListener("change", onStatusFilterChange);
    els.alertDismiss.addEventListener("click", hideAlert);
  }

  // -------------------------------------------------------------------------
  // API Calls
  // -------------------------------------------------------------------------

  /**
   * Fetch local network configuration from GET /api/network
   */
  async function loadNetworkConfig() {
    try {
      const res = await fetch("/api/network");
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Failed to load network configuration.`);
      }
      const data = await res.json();
      state.network = data;
      renderNetwork(data);
    } catch (err) {
      console.error("Network config error:", err);
      showAlert(`Network configuration error: ${err.message}`);
    }
  }

  /**
   * Check initial server status upon page load
   */
  async function checkInitialStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) return;
      const data = await res.json();
      if (data.is_scanning) {
        setScanningState(true);
        startPolling();
      } else if (data.status === "completed") {
        updateStatusBadge("completed", "Completed");
        loadDevices();
      }
    } catch (err) {
      console.warn("Status check warning:", err);
    }
  }

  /**
   * Trigger an ARP scan via POST /api/scan
   */
  async function onScanClick() {
    if (state.isScanning) return;
    hideAlert();
    setScanningState(true);

    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (res.status === 409) {
        // Scan already in progress on the server
        showAlert("A network scan is already currently running.");
        startPolling();
        return;
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || `Scan request failed with HTTP ${res.status}`);
      }

      els.scanProgressMsg.textContent = "Scanning local subnet via ARP broadcast...";
      startPolling();
    } catch (err) {
      console.error("Scan error:", err);
      setScanningState(false);
      updateStatusBadge("error", "Error");
      showAlert(`Failed to start scan: ${err.message}`);
    }
  }

  /**
   * Poll GET /api/status until scan is completed or error occurs
   */
  function startPolling() {
    if (state.pollTimer) clearInterval(state.pollTimer);

    state.pollTimer = setInterval(async () => {
      try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (!data.is_scanning) {
          // Scan finished
          clearInterval(state.pollTimer);
          state.pollTimer = null;
          setScanningState(false);

          if (data.status === "completed") {
            updateStatusBadge("completed", "Completed");
            if (data.last_scan) {
              const dur = data.last_scan.duration_seconds;
              const count = data.last_scan.device_count;
              els.statDuration.textContent = `${dur}s`;
              els.scanProgressMsg.textContent = `Scan finished in ${dur}s. Found ${count} device(s).`;
            }
            await loadDevices();
          } else {
            updateStatusBadge("error", "Error");
            let msg = data.error_message || "Scan terminated with an error.";
            if (msg.toLowerCase().includes("permission") || msg.toLowerCase().includes("winpcap") || msg.toLowerCase().includes("npcap") || msg.toLowerCase().includes("administrator")) {
              msg += " (Hint: Please ensure Npcap is installed with WinPcap-compatible mode and the terminal is Run as Administrator).";
            }
            els.scanProgressMsg.textContent = msg;
            showAlert(`Scan error: ${msg}`);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 800);
  }

  /**
   * Fetch latest discovered devices from GET /api/devices
   */
  async function loadDevices() {
    try {
      const res = await fetch("/api/devices");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      state.devices = data.devices || [];
      els.statDeviceCount.textContent = state.devices.length;

      applyFilter();
    } catch (err) {
      console.error("Load devices error:", err);
      showAlert(`Failed to retrieve discovered devices: ${err.message}`);
    }
  }

  // -------------------------------------------------------------------------
  // Filtering & Search
  // -------------------------------------------------------------------------

  function onSearchInput(e) {
    state.searchQuery = e.target.value.trim().toLowerCase();
    els.searchClear.classList.toggle("hidden", state.searchQuery.length === 0);
    applyFilter();
  }

  function onSearchClear() {
    els.searchInput.value = "";
    state.searchQuery = "";
    els.searchClear.classList.add("hidden");
    applyFilter();
  }

  function onStatusFilterChange(e) {
    state.statusFilter = e.target.value;
    applyFilter();
  }

  function applyFilter() {
    const q = state.searchQuery;
    const filterStatus = state.statusFilter;

    state.filteredDevices = state.devices.filter((dev) => {
      // Status match
      if (filterStatus !== "all" && dev.status !== filterStatus) {
        return false;
      }

      // Query match (substring across IP, MAC, hostname, custom name, manufacturer)
      if (q) {
        const ip = (dev.ip_address || "").toLowerCase();
        const mac = (dev.mac_address || "").toLowerCase();
        const host = (dev.hostname || "").toLowerCase();
        const custom = (dev.custom_name || "").toLowerCase();
        const vendor = (dev.manufacturer || "").toLowerCase();
        return ip.includes(q) || mac.includes(q) || host.includes(q) || custom.includes(q) || vendor.includes(q);
      }

      return true;
    });

    renderTable();
  }

  // -------------------------------------------------------------------------
  // Rendering
  // -------------------------------------------------------------------------

  function renderNetwork(net) {
    if (!net || !net.is_complete && !net.ip_address) {
      els.adapterName.textContent = "Unavailable";
      els.adapterType.textContent = "No active interface";
      els.localIp.textContent = "—";
      els.subnetMask.textContent = "—";
      els.gatewayIp.textContent = "—";
      els.statCidr.textContent = "—";
      return;
    }

    els.adapterName.textContent = net.interface_name || "Unknown";
    els.adapterType.textContent = "Active Adapter";
    els.localIp.textContent = net.ip_address || "—";
    els.localIpSub.textContent = "Host IPv4 Address";

    if (net.subnet_mask) {
      els.subnetMask.textContent = net.subnet_mask;
      els.subnetPrefix.textContent = net.cidr ? `CIDR: ${net.cidr}` : `Prefix /${net.prefix_length}`;
    } else {
      els.subnetMask.textContent = "—";
    }

    els.gatewayIp.textContent = net.gateway || "None";
    els.statCidr.textContent = net.cidr || "—";
  }

  function renderTable() {
    const tbody = els.devicesTbody;
    tbody.innerHTML = "";

    if (state.devices.length === 0) {
      els.tableEmpty.classList.remove("hidden");
      els.tableNoResults.classList.add("hidden");
      return;
    }

    els.tableEmpty.classList.add("hidden");

    if (state.filteredDevices.length === 0) {
      els.tableNoResults.classList.remove("hidden");
      return;
    }

    els.tableNoResults.classList.add("hidden");

    const fragment = document.createDocumentFragment();

    state.filteredDevices.forEach((dev) => {
      const tr = document.createElement("tr");

      // IP Address
      const tdIp = document.createElement("td");
      tdIp.className = "mono";
      tdIp.textContent = dev.ip_address;
      tr.appendChild(tdIp);

      // MAC Address
      const tdMac = document.createElement("td");
      tdMac.className = "mono";
      tdMac.textContent = dev.mac_address;
      tr.appendChild(tdMac);

      // Device Name / Hostname
      const tdHost = document.createElement("td");
      if (dev.custom_name) {
        tdHost.innerHTML = `
          <div class="device-name-container">
            <span class="device-custom-name">${escapeHtml(dev.custom_name)}</span>
            ${dev.hostname ? `<span class="device-hostname-sub">${escapeHtml(dev.hostname)}</span>` : ""}
          </div>
        `;
      } else if (dev.hostname) {
        tdHost.innerHTML = `
          <div class="device-name-container">
            <span class="device-hostname-main">${escapeHtml(dev.hostname)}</span>
          </div>
        `;
      } else if (dev.manufacturer && dev.manufacturer.includes("Private MAC")) {
        tdHost.innerHTML = `
          <div class="device-name-container">
            <span class="device-name-placeholder">Private Device</span>
          </div>
        `;
      } else {
        tdHost.innerHTML = '<span class="text-subtle">Unresolved</span>';
      }
      tr.appendChild(tdHost);

      // Manufacturer
      const tdVendor = document.createElement("td");
      if (dev.manufacturer) {
        tdVendor.innerHTML = `<span class="vendor-badge">${escapeHtml(dev.manufacturer)}</span>`;
      } else {
        tdVendor.innerHTML = '<span class="text-subtle">Unknown</span>';
      }
      tr.appendChild(tdVendor);

      // Status
      const tdStatus = document.createElement("td");
      if (dev.status === "offline") {
        tdStatus.innerHTML = '<span class="pill pill-offline">Offline</span>';
      } else {
        tdStatus.innerHTML = '<span class="pill pill-online">Online</span>';
      }
      tr.appendChild(tdStatus);

      // Action / Rename Button
      const tdAction = document.createElement("td");
      tdAction.style.textAlign = "right";
      const renameBtn = document.createElement("button");
      renameBtn.className = "btn-rename";
      renameBtn.title = "Set custom friendly nickname";
      renameBtn.innerHTML = `<span>✏️</span> <span>Name</span>`;
      renameBtn.addEventListener("click", () => onRenameClick(dev));
      tdAction.appendChild(renameBtn);
      tr.appendChild(tdAction);

      fragment.appendChild(tr);
    });

    tbody.appendChild(fragment);
  }

  /**
   * Prompt user to enter or edit a friendly nickname for a device
   */
  async function onRenameClick(dev) {
    const currentName = dev.custom_name || "";
    const promptMsg = `Set friendly nickname for device:\nIP: ${dev.ip_address}\nMAC: ${dev.mac_address}\n\nExamples: "My Phone", "Living Room TV", "Home Router"`;
    const newName = prompt(promptMsg, currentName);
    if (newName === null) return; // Cancelled

    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(dev.mac_address)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ custom_name: newName.trim() }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${res.status}`);
      }

      await loadDevices();
    } catch (err) {
      console.error("Rename device error:", err);
      showAlert(`Failed to update device nickname: ${err.message}`);
    }
  }

  function setScanningState(isScanning) {
    state.isScanning = isScanning;
    els.scanBtn.disabled = isScanning;
    els.scanSpinner.classList.toggle("hidden", !isScanning);

    if (isScanning) {
      els.scanBtnText.textContent = "Scanning...";
      updateStatusBadge("scanning", "Scanning...");
      els.scanProgressMsg.textContent = "ARP broadcast in progress...";
    } else {
      els.scanBtnText.textContent = "Scan Network";
    }
  }

  function updateStatusBadge(type, label) {
    els.statusBadge.className = `status-badge badge-${type}`;
    els.statusText.textContent = label;
  }

  function showAlert(msg) {
    els.alertMessage.textContent = msg;
    els.alertBanner.classList.remove("hidden");
  }

  function hideAlert() {
    els.alertBanner.classList.add("hidden");
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Run on page load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
