// =========================================================
// i18n.js — Language management for web_exporter
// =========================================================

const LANG_DICT = {
    vi: {
        title: "🚀 qBittorrent Queue Exporter",
        subtitle: "Xuất torrent vào hàng đợi Upload-Assistant",
        settings_title: "⚙️ Cài đặt Kết nối qBittorrent API (WebUI)",
        url_label: "URL WebUI (Mặc định: http://localhost:8080)",
        user_label: "Tài khoản (Username)",
        pass_label: "Mật khẩu (Password)",
        btn_test: "Kiểm tra Kết nối",
        btn_save: "Lưu cài đặt &amp; Tải lại",
        api_status: "Trạng thái API:",
        cat_label: "1. Chọn Danh mục",
        cat_all: "🌐 Tất cả torrent",
        queue_label: "2. Nhập Tên Queue Log",
        queue_hint: "Tên file log, ví dụ: 'vmf' -> vmf_queue.log",
        status_filter_label: "📋 Trạng thái",
        sort_label: "🔀 Sắp xếp",
        reverse_label: "Đảo thứ tự",
        tag_label: "🏷️ Tags",
        tracker_label: "📡 Tracker",
        tracker_hint: "Include: chỉ giữ torrent thuộc tracker đã chọn. Exclude: bỏ qua torrent thuộc tracker đã chọn.",
        mode_include: "✅ Include",
        mode_exclude: "🚫 Exclude",
        advanced_filters: "🔧 Bộ lọc nâng cao",
        min_size_label: "📏 Kích thước tối thiểu",
        max_size_label: "📏 Kích thước tối đa",
        added_after_label: "📅 Chỉ lấy torrent thêm sau ngày",
        name_pattern_label: "🔍 Lọc theo tên (regex hoặc substring)",
        limit_label: "🔢 Giới hạn số torrent",
        only_completed: "CHỈ xuất những torrent đã Tải xong (100%)",
        btn_export: "Kéo dữ liệu và Đưa vào Hàng đợi",
        exclude_tracker_label: "🚫 Loại trừ Tracker",
        exclude_tracker_hint: "Torrent thuộc tracker được chọn sẽ bị bỏ qua khi xuất hàng đợi.",
        status_ok: "Thành công!",
        status_err: "Lỗi!",
        sys_err: "Lỗi hệ thống:",
        test_ok: "✅ Kết nối thành công! Đã tìm thấy",
        cat_found: "danh mục.",
        save_err: "Lỗi lưu cấu hình!",
        msg_added: "Đã thêm",
        msg_ignored: "torrent mới vào hàng đợi. Bỏ qua",
        msg_dupes: "torrent trùng/đã xử lý.",
        msg_excluded: "torrent bị loại trừ do tracker.",
        run_title: "▶️ Chạy Upload Assistant",
        run_desc: 'Sau khi xuất hàng đợi thành công, bạn có thể chạy <kbd>upload.py</kbd> ngay tại đây. Script sẽ tự động thêm <code>--queue [Tên Queue]</code> vào câu lệnh.',
        args_label: "Tham số tùy chỉnh (Arguments):",
        btn_run: "Bắt đầu Chạy Upload ngay trên Web",
        btn_stop: "Dừng Upload đang chạy",
        run_ok: "Đã khởi chạy Upload Assistant thành công! Đang lấy Log...",
        open_external: "Mở trong cửa sổ CMD riêng (không xem log trên web)",
        run_ok_ext: "Đã khởi chạy Upload Assistant trong cửa sổ CMD riêng. Hãy xem tiến trình trực tiếp trong cửa sổ đó.",
        stdin_label: "Gửi lệnh tới upload.py (stdin):",
        stdin_placeholder: "Nhập lệnh rồi Enter hoặc bấm Gửi...",
        stdin_send: "Gửi",
        stop_ok: "Tiến trình Upload đã được dừng theo yêu cầu.",
    },
    en: {
        title: "🚀 qBittorrent Queue Exporter",
        subtitle: "Export torrents to Upload-Assistant queue",
        settings_title: "⚙️ qBittorrent API (WebUI) Settings",
        url_label: "WebUI URL (Default: http://localhost:8080)",
        user_label: "Username",
        pass_label: "Password",
        btn_test: "Test Connection",
        btn_save: "Save &amp; Reload",
        api_status: "API Status:",
        cat_label: "1. Select Categories",
        cat_all: "🌐 All torrents",
        queue_label: "2. Queue Log Name",
        queue_hint: "Log prefix, e.g. 'vmf' -> vmf_queue.log",
        status_filter_label: "📋 Status Filter",
        sort_label: "🔀 Sort By",
        reverse_label: "Reverse Order",
        tag_label: "🏷️ Tags",
        tracker_label: "📡 Tracker",
        tracker_hint: "Include: only keep torrents from selected trackers. Exclude: skip torrents from selected trackers.",
        mode_include: "✅ Include",
        mode_exclude: "🚫 Exclude",
        advanced_filters: "🔧 Advanced Filters",
        min_size_label: "📏 Minimum Size",
        max_size_label: "📏 Maximum Size",
        added_after_label: "📅 Only torrents added after",
        name_pattern_label: "🔍 Filter by name (regex or substring)",
        limit_label: "🔢 Limit number of torrents",
        only_completed: "ONLY export Completed torrents (100%)",
        btn_export: "Fetch Data and Send to Queue",
        exclude_tracker_label: "🚫 Exclude Tracker",
        exclude_tracker_hint: "Torrents belonging to the selected tracker(s) will be excluded from the queue.",
        status_ok: "Success!",
        status_err: "Error!",
        sys_err: "System Error:",
        test_ok: "✅ Connected successfully! Found",
        cat_found: "categories.",
        save_err: "Failed to save configuration!",
        msg_added: "Added",
        msg_ignored: "new torrents to queue. Ignored",
        msg_dupes: "duplicate/processed torrents.",
        msg_excluded: "torrents excluded by tracker.",
        run_title: "▶️ Run Upload Assistant",
        run_desc: 'After exporting, you can execute <kbd>upload.py</kbd> directly from here. The script will automatically append <code>--queue [Queue Name]</code> to the command.',
        args_label: "Custom Arguments:",
        btn_run: "Start Upload Process right here",
        btn_stop: "Stop running Upload",
        run_ok: "Upload Assistant launched successfully! Fetching logs...",
        open_external: "Open in a separate CMD window (no logs in web UI)",
        run_ok_ext: "Upload Assistant started in a separate CMD window. Please watch progress in that window.",
        stdin_label: "Send input to upload.py (stdin):",
        stdin_placeholder: "Type command then Enter or click Send...",
        stdin_send: "Send",
        stop_ok: "Upload process has been stopped as requested.",
    }
};

let CURRENT_LANG = localStorage.getItem("appLang") || "vi";

function changeLanguage(langCode) {
    CURRENT_LANG = langCode;
    localStorage.setItem("appLang", langCode);
    const langSelect = document.getElementById("langSelect");
    if (langSelect) langSelect.value = langCode;

    const trans = LANG_DICT[langCode];
    if (!trans) return;

    // Update all data-lang elements
    document.querySelectorAll("[data-lang]").forEach((el) => {
        const key = el.getAttribute("data-lang");
        if (trans[key]) el.innerHTML = trans[key];
    });

    // Update placeholders
    document.querySelectorAll("[data-lang-placeholder]").forEach((el) => {
        const key = el.getAttribute("data-lang-placeholder");
        if (trans[key]) el.setAttribute("placeholder", trans[key]);
    });

    // Dynamic status translation
    const statusEl = document.getElementById("dynamic_status");
    if (statusEl) {
        if (statusEl.textContent === "Chưa kết nối" && langCode === "en")
            statusEl.textContent = "Not connected";
        if (statusEl.textContent === "Not connected" && langCode === "vi")
            statusEl.textContent = "Chưa kết nối";
    }
}

// Apply initial language
changeLanguage(CURRENT_LANG);
