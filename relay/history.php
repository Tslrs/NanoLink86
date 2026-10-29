<?php
/**
 * NanoLink86 - Audit & History Dashboard (PHP Edition)
 * Tracks user logins, originating devices (iPhone, Mac, iPad, etc.), 
 * timestamps, and all executed DOS commands sent to Tang Nano 9K FPGA.
 * Compatible with University Server & Local PHP.
 */

date_default_timezone_set('Europe/Athens');
error_reporting(E_ALL & ~E_DEPRECATED);

$log_file = __DIR__ . '/audit_log.json';

// Initialize log structure if file doesn't exist
if (!file_exists($log_file)) {
    $init_data = [
        'logins' => [],
        'commands' => []
    ];
    file_put_contents($log_file, json_encode($init_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// Function to load log data
function load_audit_log($file) {
    if (!file_exists($file)) return ['logins' => [], 'commands' => []];
    $content = file_get_contents($file);
    $data = json_decode($content, true);
    return is_array($data) ? $data : ['logins' => [], 'commands' => []];
}

// Function to save log data
function save_audit_log($file, $data) {
    return file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
}

// Helper to parse device friendly name from User-Agent
function parse_device($ua) {
    $ua_low = strtolower($ua);
    if (strpos($ua_low, 'iphone') !== false) {
        return 'Apple iPhone';
    } elseif (strpos($ua_low, 'ipad') !== false) {
        return 'Apple iPad';
    } elseif (strpos($ua_low, 'android') !== false) {
        return 'Android Device';
    } elseif (strpos($ua_low, 'macintosh') !== false || strpos($ua_low, 'mac os') !== false) {
        return 'Apple Mac';
    } elseif (strpos($ua_low, 'windows') !== false) {
        return 'Windows PC';
    } elseif (strpos($ua_low, 'linux') !== false) {
        return 'Linux PC';
    }
    return 'Web Client';
}

function get_device_icon($device, $size = 14) {
    $d = strtolower($device);
    // Apple (iPhone, Mac, iPad) - Official Bitten Apple Logo
    if (strpos($d, 'apple') !== false || strpos($d, 'iphone') !== false || strpos($d, 'mac') !== false || strpos($d, 'ipad') !== false) {
        return '<svg class="brand-svg svg-apple" width="'.$size.'" height="'.$size.'" viewBox="0 0 24 24"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 4.15c.66-.8 1.11-1.92.99-3.04-1 .04-2.15.65-2.83 1.45-.6.7-1.13 1.83-1 2.94 1.12.09 2.22-.57 2.84-1.35z"/></svg>';
    }
    // Android - Official Bugdroid Robot
    if (strpos($d, 'android') !== false) {
        return '<svg class="brand-svg svg-android" width="'.$size.'" height="'.$size.'" viewBox="0 0 24 24"><path d="M6 18c0 .55.45 1 1 1h1v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h4v3.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V19h1c.55 0 1-.45 1-1V8H6v10zM3.5 8C2.67 8 2 8.67 2 9.5v7c0 .83.67 1.5 1.5 1.5S5 17.33 5 16.5v-7C5 8.67 4.33 8 3.5 8zm17 0c-.83 0-1.5.67-1.5 1.5v7c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5v-7c0-.83-.67-1.5-1.5-1.5zm-4.97-4.84l1.3-1.3a.5.5 0 00-.71-.71L14.7 2.57A6.47 6.47 0 0012 2c-.98 0-1.9.22-2.7.57L7.88.94a.5.5 0 00-.71.71l1.3 1.3C6.72 4.14 5.5 6.09 5.5 8.35h13c0-2.26-1.22-4.21-2.97-5.19zM9 6a1 1 0 110-2 1 1 0 010 2zm6 0a1 1 0 110-2 1 1 0 010 2z"/></svg>';
    }
    // Windows - Official 4-Pane Logo
    if (strpos($d, 'windows') !== false) {
        return '<svg class="brand-svg svg-windows" width="'.$size.'" height="'.$size.'" viewBox="0 0 88 88"><path d="M0 12.402l35.688-4.86.016 34.423-35.67.202zm35.67 33.527l.034 34.469-35.67-4.9-.034-29.569zm4.33-39.043L87.95 0l.05 41.525-48 .275zm48.016 45.029L88 88l-47.966-6.789-.034-34.98z"/></svg>';
    }
    // Linux - Official Multi-Color Tux Penguin Mascot
    if (strpos($d, 'linux') !== false) {
        return '<svg class="brand-svg svg-linux" width="'.$size.'" height="'.$size.'" viewBox="100 80 312 360" fill="#222226"><g transform="matrix(2 0 0 2 256 256)"><path d="M-32-25c-3 7-24 29-22 51 8 92 36 30 78 53 0 0 75-42 15-110-17-24-2-43-13-59s-30-17-44-2 6 37-14 67" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/><path d="M42 21s9-18-8-31c16 17 6 32 6 32h-3C36-13 27 6 14-56 29-73 0-88 0-60h-9c1-24-20-12-8 5-1 37-23 52-23 78-7-18 6-32 6-32s-18 15-7 37 31 17 17 27c22 15 56 5 55-27 1-8 22-5 24-3s-3-4-13-4m-56-78c-7-2-5-11-2-11s8 7 2 11m19 1c-5-7-1-14 4-13s5 13-4 13" fill="#FFFFFF"/><g fill="#FFA000" stroke="#1A1A1A" stroke-width="1"><path d="M-41 31l21 30c11 7 5 35-25 21-17-5-31-4-33-13s4-10 3-14c-4-22 14-11 19-22s5-16 15-2M71 45c-4-6 0-17-14-16-6 12-23 24-24 0-10 0-3 24-7 35-9 27 17 29 28 16l26-18c2-3 5-6-9-17m-92-92c-3-6 11-14 16-14s12 4 19 6 4 9 2 10S3-35-5-35s-10-8-16-12"/><path d="M-21-48c8 6 17 11 35-3"/></g><path d="M-10-54c-2 0 1-2 2-1m7 1c1-1-1-2-3-1" fill="#FFFFFF"/></g></svg>';
    }
    // Generic Web Client / Browser
    return '<svg class="brand-svg svg-web" width="'.$size.'" height="'.$size.'" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>';
}

// --- HANDLE POST API (For Server or external webhooks) ---
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $raw_input = file_get_contents('php://input');
    $post_data = json_decode($raw_input, true);
    if (!$post_data) {
        $post_data = $_POST;
    }

    $action = $post_data['action'] ?? '';
    $log_data = load_audit_log($log_file);

    if ($action === 'login') {
        $ua = $post_data['user_agent'] ?? ($_SERVER['HTTP_USER_AGENT'] ?? 'Unknown');
        $ip = $post_data['ip'] ?? ($_SERVER['REMOTE_ADDR'] ?? '127.0.0.1');
        $device = $post_data['device'] ?? parse_device($ua);
        $status = $post_data['status'] ?? 'Authenticated (PIN 1986)';

        $entry = [
            'id' => count($log_data['logins']) + 1,
            'timestamp' => date('Y-m-d H:i:s'),
            'device' => $device,
            'ip' => $ip,
            'status' => $status,
            'user_agent' => $ua
        ];
        $log_data['logins'][] = $entry;
        save_audit_log($log_file, $log_data);

        header('Content-Type: application/json');
        echo json_encode(['status' => 'success', 'entry' => $entry]);
        exit;
    }

    if ($action === 'command') {
        $cmd = trim($post_data['command'] ?? '');
        $device = $post_data['device'] ?? 'Unknown Device';
        $ip = $post_data['ip'] ?? ($_SERVER['REMOTE_ADDR'] ?? '127.0.0.1');

        if (!empty($cmd)) {
            $entry = [
                'id' => count($log_data['commands']) + 1,
                'timestamp' => date('Y-m-d H:i:s'),
                'command' => $cmd,
                'device' => $device,
                'ip' => $ip,
                'target' => 'Tang Nano 9K PS/2'
            ];
            $log_data['commands'][] = $entry;
            save_audit_log($log_file, $log_data);

            header('Content-Type: application/json');
            echo json_encode(['status' => 'success', 'entry' => $entry]);
            exit;
        }
    }

    if ($action === 'clear') {
        save_audit_log($log_file, ['logins' => [], 'commands' => []]);
        header('Location: ' . $_SERVER['PHP_SELF']);
        exit;
    }
}

// --- HANDLE EXPORT ---
if (isset($_GET['export'])) {
    $log_data = load_audit_log($log_file);

    if ($_GET['export'] === 'json') {
        header('Content-Type: application/json');
        header('Content-Disposition: attachment; filename="nanolink86_audit_' . date('Ymd_His') . '.json"');
        echo json_encode($log_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        exit;
    }

    if ($_GET['export'] === 'csv') {
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename="nanolink86_commands_' . date('Ymd_His') . '.csv"');
        $out = fopen('php://output', 'w');
        fputcsv($out, ['ID', 'Timestamp', 'Command', 'Device', 'Client IP', 'Hardware Target'], ',', '"', "\\");
        foreach ($log_data['commands'] as $c) {
            fputcsv($out, [$c['id'], $c['timestamp'], $c['command'], $c['device'], $c['ip'], $c['target'] ?? 'Tang Nano 9K'], ',', '"', "\\");
        }
        fclose($out);
        exit;
    }
}

// Load logs for display
$log_data = load_audit_log($log_file);
$logins = array_reverse($log_data['logins'] ?? []);
$commands = array_reverse($log_data['commands'] ?? []);

$total_logins = count($logins);
$total_commands = count($commands);

// Count unique devices
$device_counts = [];
foreach ($log_data['logins'] as $l) {
    $d = $l['device'] ?? 'Unknown';
    $device_counts[$d] = ($device_counts[$d] ?? 0) + 1;
}

$last_activity = 'None';
if (!empty($commands)) {
    $last_activity = $commands[0]['timestamp'];
} elseif (!empty($logins)) {
    $last_activity = $logins[0]['timestamp'];
}

// Device filter
$filter_device = $_GET['device'] ?? 'all';
if ($filter_device !== 'all') {
    $commands = array_filter($commands, function($c) use ($filter_device) {
        return stripos($c['device'], $filter_device) !== false;
    });
    $logins = array_filter($logins, function($l) use ($filter_device) {
        return stripos($l['device'], $filter_device) !== false;
    });
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>NanoLink86 • Audit & History Dashboard (PHP)</title>
<style>
  :root {
    --bg-main: #0B0B0E;
    --card-bg: rgba(24, 24, 28, 0.78);
    --border-color: rgba(255, 255, 255, 0.1);
    --text-primary: #FFFFFF;
    --text-secondary: rgba(235, 235, 245, 0.65);
    --text-tertiary: rgba(235, 235, 245, 0.4);
    --apple-blue: #0A84FF;
    --apple-green: #30D158;
    --apple-purple: #BF5AF2;
    --apple-orange: #FF9F0A;
    --apple-red: #FF453A;
  }

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif;
  }

  body {
    background: var(--bg-main);
    color: var(--text-primary);
    min-height: 100vh;
    padding: 24px 16px 60px 16px;
    display: flex;
    justify-content: center;
  }

  .container {
    width: 100%;
    max-width: 920px;
  }

  /* HEADER */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .brand-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-icon {
    width: 42px;
    height: 42px;
    background: linear-gradient(135deg, #1D4ED8, #0A84FF);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 20px rgba(10, 132, 255, 0.35);
  }
  .brand-icon svg { width: 22px; height: 22px; fill: #FFF; }
  .title-wrap h1 {
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.4px;
  }
  .title-wrap p {
    font-size: 12px;
    color: var(--text-secondary);
  }

  .actions-group {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .btn {
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 9px;
    text-decoration: none;
    cursor: pointer;
    border: none;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-primary {
    background: var(--apple-blue);
    color: #FFF;
  }
  .btn-secondary {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid var(--border-color);
    color: #FFF;
  }
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.14);
  }
  .btn-danger {
    background: rgba(255, 69, 58, 0.16);
    border: 1px solid rgba(255, 69, 58, 0.35);
    color: #FFA29C;
  }

  /* METRICS GRID */
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }
  .metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 16px 18px;
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
  }
  .metric-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: var(--text-tertiary);
    margin-bottom: 6px;
  }
  .metric-value {
    font-size: 24px;
    font-weight: 700;
    font-family: ui-monospace, "SF Mono", monospace;
    letter-spacing: -0.5px;
    color: #FFF;
  }
  .metric-sub {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  /* SECTION CARDS */
  .section-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 24px;
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
  }
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    flex-wrap: wrap;
    gap: 10px;
  }
  .section-title {
    font-size: 16px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .badge {
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
  }
  .badge-blue { background: rgba(10, 132, 255, 0.2); color: #93C5FD; }
  .badge-green { background: rgba(48, 209, 88, 0.2); color: #86EFAC; }
  .badge-purple { background: rgba(191, 90, 242, 0.2); color: #E9D5FF; }

  /* FILTER BAR */
  .filter-bar {
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
  }
  .filter-pill {
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .filter-pill:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #FFF;
  }
  .filter-pill.active {
    background: var(--apple-blue);
    border-color: rgba(255, 255, 255, 0.2);
    color: #FFF;
  }

  /* TABLES */
  .table-wrap {
    width: 100%;
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }
  th {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--text-tertiary);
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  td {
    padding: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    color: var(--text-secondary);
  }
  tr:last-child td {
    border-bottom: none;
  }
  tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }

  .time-cell {
    font-family: ui-monospace, "SF Mono", monospace;
    font-size: 12px;
    color: var(--text-tertiary);
    white-space: nowrap;
  }
  .cmd-tag {
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 12px;
    font-weight: 700;
    color: #34D399;
    background: rgba(52, 211, 153, 0.12);
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid rgba(52, 211, 153, 0.25);
    display: inline-block;
  }
  .device-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #FFF;
  }
  .device-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    flex-shrink: 0;
  }
  .brand-svg {
    display: block;
    flex-shrink: 0;
  }
  .svg-apple { fill: #F5F5F7; filter: drop-shadow(0 1px 2px rgba(255, 255, 255, 0.25)); }
  .svg-android { fill: #3DDC84; filter: drop-shadow(0 1px 3px rgba(61, 220, 132, 0.4)); }
  .svg-windows { fill: #00ADEF; filter: drop-shadow(0 1px 3px rgba(0, 173, 239, 0.4)); }
  .svg-linux { filter: drop-shadow(0 1px 3px rgba(255, 160, 0, 0.4)); }
  .svg-web { fill: #9CA3AF; }
  .ip-tag {
    font-family: ui-monospace, "SF Mono", monospace;
    font-size: 11px;
    color: var(--text-tertiary);
  }

  /* FOOTER */
  .footer {
    text-align: center;
    font-size: 11px;
    color: var(--text-tertiary);
    margin-top: 20px;
  }
  .footer a {
    color: var(--apple-blue);
    text-decoration: none;
  }
</style>
</head>
<body>

<div class="container">
  <!-- TOP HEADER -->
  <div class="header">
    <div class="brand-group">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
      </div>
      <div class="title-wrap">
        <h1>NanoLink86 Audit &amp; History</h1>
        <p>Device Tracking &amp; DOS Command Logging System</p>
      </div>
    </div>

    <div class="actions-group">
      <a href="?export=csv" class="btn btn-secondary">📥 Export CSV</a>
      <a href="?export=json" class="btn btn-secondary">💾 Export JSON</a>
      <form method="POST" style="display:inline;" onsubmit="return confirm('Clear entire audit history?');">
        <input type="hidden" name="action" value="clear">
        <button type="submit" class="btn btn-danger">🗑️ Clear</button>
      </form>
    </div>
  </div>

  <!-- SUMMARY METRICS -->
  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-title">Total Logins</div>
      <div class="metric-value"><?= number_format($total_logins) ?></div>
      <div class="metric-sub">Session authentications</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Commands Sent</div>
      <div class="metric-value"><?= number_format($total_commands) ?></div>
      <div class="metric-sub">Executed on FreeDOS</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Active Devices</div>
      <div class="metric-value"><?= count($device_counts) ?></div>
      <div class="metric-sub"><?php 
        $dev_str = [];
        foreach ($device_counts as $dev => $cnt) $dev_str[] = "$dev ($cnt)";
        echo !empty($dev_str) ? htmlspecialchars(implode(', ', array_slice($dev_str, 0, 2))) : 'None';
      ?></div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Last Activity</div>
      <div class="metric-value" style="font-size: 15px; padding-top: 5px;"><?= $last_activity !== 'None' ? date('H:i:s d/m', strtotime($last_activity)) : 'Idle' ?></div>
      <div class="metric-sub">Athens Local Time</div>
    </div>
  </div>

  <!-- SECTION 1: EXECUTED COMMANDS AUDIT -->
  <div class="section-card">
    <div class="section-header">
      <div class="section-title">
        <span>⌨️ Executed DOS Commands</span>
        <span class="badge badge-green"><?= count($commands) ?> entries</span>
      </div>

      <div class="filter-bar">
        <span style="font-size: 11px; color: var(--text-tertiary);">Device:</span>
        <a href="?device=all" class="filter-pill <?= $filter_device === 'all' ? 'active' : '' ?>">All</a>
        <a href="?device=iphone" class="filter-pill <?= $filter_device === 'iphone' ? 'active' : '' ?>"><?= get_device_icon('iphone', 12) ?> iPhone</a>
        <a href="?device=mac" class="filter-pill <?= $filter_device === 'mac' ? 'active' : '' ?>"><?= get_device_icon('mac', 12) ?> Mac</a>
        <a href="?device=android" class="filter-pill <?= $filter_device === 'android' ? 'active' : '' ?>"><?= get_device_icon('android', 12) ?> Android</a>
        <a href="?device=linux" class="filter-pill <?= $filter_device === 'linux' ? 'active' : '' ?>"><?= get_device_icon('linux', 12) ?> Linux</a>
        <a href="?device=windows" class="filter-pill <?= $filter_device === 'windows' ? 'active' : '' ?>"><?= get_device_icon('windows', 12) ?> Windows</a>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Command</th>
            <th>Device Origin</th>
            <th>Client IP</th>
            <th>Target Hardware</th>
          </tr>
        </thead>
        <tbody>
          <?php if (empty($commands)): ?>
            <tr>
              <td colspan="5" style="text-align: center; padding: 24px; color: var(--text-tertiary);">
                No DOS commands logged yet. Type commands in Safari to see them appear here!
              </td>
            </tr>
          <?php else: ?>
            <?php foreach ($commands as $cmd): ?>
              <tr>
                <td class="time-cell"><?= htmlspecialchars($cmd['timestamp']) ?></td>
                <td><span class="cmd-tag"><?= htmlspecialchars($cmd['command']) ?></span></td>
                <td>
                  <div class="device-cell">
                    <span class="device-icon"><?= get_device_icon($cmd['device'] ?? '') ?></span>
                    <span><?= htmlspecialchars($cmd['device']) ?></span>
                  </div>
                </td>
                <td class="ip-tag"><?= htmlspecialchars($cmd['ip']) ?></td>
                <td><span class="badge badge-blue"><?= htmlspecialchars($cmd['target'] ?? 'Tang Nano 9K') ?></span></td>
              </tr>
            <?php endforeach; ?>
          <?php endif; ?>
        </tbody>
      </table>
    </div>
  </div>

  <!-- SECTION 2: LOGIN HISTORY -->
  <div class="section-card">
    <div class="section-header">
      <div class="section-title">
        <span>🔐 Authentication &amp; Login History</span>
        <span class="badge badge-purple"><?= count($logins) ?> entries</span>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Device / Platform</th>
            <th>Client IP</th>
            <th>Status</th>
            <th>User Agent</th>
          </tr>
        </thead>
        <tbody>
          <?php if (empty($logins)): ?>
            <tr>
              <td colspan="5" style="text-align: center; padding: 24px; color: var(--text-tertiary);">
                No login events recorded yet.
              </td>
            </tr>
          <?php else: ?>
            <?php foreach ($logins as $login): ?>
              <tr>
                <td class="time-cell"><?= htmlspecialchars($login['timestamp']) ?></td>
                <td>
                  <div class="device-cell">
                    <span class="device-icon"><?= get_device_icon($login['device'] ?? '') ?></span>
                    <span><?= htmlspecialchars($login['device']) ?></span>
                  </div>
                </td>
                <td class="ip-tag"><?= htmlspecialchars($login['ip']) ?></td>
                <td>
                  <span class="badge badge-green"><?= htmlspecialchars($login['status']) ?></span>
                </td>
                <td style="font-size: 11px; color: var(--text-tertiary); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  <?= htmlspecialchars($login['user_agent'] ?? '') ?>
                </td>
              </tr>
            <?php endforeach; ?>
          <?php endif; ?>
        </tbody>
      </table>
    </div>
  </div>

  <div class="footer">
    NanoLink86 Project • University of Western Macedonia (UoWM) • Remote PS/2 Co-Processor<br>
    Auto-refreshing every 5 seconds &bull; <a href="http://localhost:8088" target="_blank">Open Remote Console ➔</a>
  </div>
</div>

<script>
// Auto-refresh page every 5 seconds to show new commands live
setTimeout(function() {
  window.location.reload();
}, 5000);
</script>
</body>
</html>
