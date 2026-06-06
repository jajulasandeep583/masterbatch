frappe.pages['manufacturing-cockpit'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper, title: '🏭 Manufacturing Cockpit', single_column: true
    });
    page.set_primary_action('Refresh', () => load(), 'refresh');
    const $body = $(page.body);
    $(wrapper).find('.layout-main-section').css({ 'background': '#f4eef8' });

    const fmt = (n) => (n || 0).toLocaleString('en-IN');
    const money = (n) => '₹ ' + (n || 0).toLocaleString('en-IN');

    function kpi(value, label, sub, grad) {
        return `<div style="background:${grad};border-radius:16px;padding:20px 22px;color:#fff;
            box-shadow:0 8px 22px rgba(40,10,55,.18);min-height:118px;display:flex;flex-direction:column;justify-content:space-between;">
            <div style="font-size:13px;opacity:.92;font-weight:600;letter-spacing:.3px">${label}</div>
            <div><div style="font-size:30px;font-weight:800;line-height:1.1">${value}</div>
            <div style="font-size:12px;opacity:.85;margin-top:2px">${sub || ''}</div></div></div>`;
    }

    function section(title, inner) {
        return `<div style="background:#fff;border-radius:16px;padding:20px 22px;margin-top:18px;
            box-shadow:0 6px 18px rgba(40,10,55,.08)">
            <div style="font-size:17px;font-weight:800;color:#3a1145;margin-bottom:14px">${title}</div>${inner}</div>`;
    }

    function badge(s) {
        const ok = s === 'Passed';
        return `<span style="padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;
            background:${ok ? '#e3f6e9' : '#fde4e4'};color:${ok ? '#1d8a3e' : '#c0392b'}">${s || 'Pending'}</span>`;
    }

    function load() {
        $body.html('<div style="padding:60px;text-align:center;color:#999">Loading manufacturing data…</div>');
        frappe.call({ method: 'masterbatch.api.cockpit_data', callback: (r) => render(r.message || {}) });
    }

    function render(d) {
        const G = {
            purple: 'linear-gradient(135deg,#7B2D8B,#4A1259)',
            teal: 'linear-gradient(135deg,#00A9A5,#007e7b)',
            orange: 'linear-gradient(135deg,#E07B00,#b35f00)',
            green: 'linear-gradient(135deg,#2BA84A,#1e7d34)',
            blue: 'linear-gradient(135deg,#2D6CDF,#1b4ea8)',
            pink: 'linear-gradient(135deg,#C2185B,#7d0f3a)',
            slate: 'linear-gradient(135deg,#5B5B6B,#33333f)',
            gold: 'linear-gradient(135deg,#C9A227,#8a6f10)'
        };

        const kpis = `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
            ${kpi(fmt(d.today_output) + ' kg', "Today's Output", fmt(d.today_batches) + ' batches today', G.purple)}
            ${kpi(fmt(d.month_output) + ' kg', 'Output This Month', fmt(d.month_batches) + ' batches', G.teal)}
            ${kpi(fmt(d.month_consumed) + ' kg', 'Raw Material Consumed', 'this month', G.orange)}
            ${kpi(money(d.fg_stock_value), 'Finished Goods Stock', fmt(d.fg_stock_qty) + ' kg in store', G.green)}
            ${kpi(fmt(d.pending_deliveries), 'Orders to Deliver', money(d.pending_value) + ' pending', G.pink)}
            ${kpi(fmt(d.open_pos), 'Open Purchase Orders', 'awaiting material', G.blue)}
            ${kpi(d.qc_rate + '%', 'QC Pass Rate', fmt(d.qc_failed) + ' failed batches', G.gold)}
            ${kpi(fmt(d.total_batches), 'Total Batches', 'all time', G.slate)}
        </div>`;

        // pending deliveries table
        let so = '<div style="color:#999">No pending deliveries 🎉</div>';
        if ((d.pending_so || []).length) {
            so = `<table style="width:100%;border-collapse:collapse;font-size:13px">
                <tr style="text-align:left;color:#7B2D8B;border-bottom:2px solid #efe7f3">
                  <th style="padding:8px">Order</th><th>Customer</th><th>Item</th><th>Qty</th><th>Delivery Date</th><th>Delivered</th></tr>
                ${d.pending_so.map(r => `<tr style="border-bottom:1px solid #f3eef7">
                  <td style="padding:8px"><a href="/app/sales-order/${r.name}">${r.name}</a></td>
                  <td>${r.customer}</td><td>${r.item_code}</td><td>${fmt(r.qty)} kg</td>
                  <td>${frappe.datetime.str_to_user(r.delivery_date) || '-'}</td>
                  <td>${Math.round(r.per || 0)}%</td></tr>`).join('')}
            </table>`;
        }

        // top shades bars
        const mx = 1;
        let bars = (d.top_shades || []).map(t => `
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:9px">
              <div style="width:80px;font-weight:700;color:#3a1145;font-size:13px">${t.shade_code}</div>
              <div style="flex:1;background:#efe7f3;border-radius:8px;height:20px;overflow:hidden">
                <div style="width:${t.pct}%;height:100%;background:linear-gradient(90deg,#7B2D8B,#00A9A5);border-radius:8px"></div></div>
              <div style="width:90px;text-align:right;color:#777;font-size:12px">${fmt(t.o)} kg</div>
            </div>`).join('');
        if (!bars) bars = '<div style="color:#999">No production yet</div>';

        // recent batches
        let rec = `<table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr style="text-align:left;color:#7B2D8B;border-bottom:2px solid #efe7f3">
              <th style="padding:8px">Batch</th><th>Date</th><th>Item</th><th>Shade</th><th>Output</th><th>QC</th></tr>
            ${(d.recent || []).map(r => `<tr style="border-bottom:1px solid #f3eef7">
              <td style="padding:8px"><a href="/app/batch-production-sheet/${r.batch_no}">${r.batch_no}</a></td>
              <td>${frappe.datetime.str_to_user(r.production_date)}</td>
              <td>${r.finished_item}</td><td>${r.shade_code || '-'}</td>
              <td>${fmt(r.actual_output_kg)} kg</td><td>${badge(r.qc_status)}</td></tr>`).join('')}
        </table>`;

        const quick = `<div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:6px">
            ${qbtn('New Batch', '/app/batch-production-sheet/new', '#7B2D8B')}
            ${qbtn('Lab Formulations', '/app/lab-formulation', '#00A9A5')}
            ${qbtn('Sales Orders', '/app/sales-order', '#E07B00')}
            ${qbtn('Stock Balance', '/app/query-report/Stock Balance', '#2BA84A')}
            ${qbtn('Production Summary', '/app/query-report/Production Summary', '#2D6CDF')}
            ${qbtn('Dashboard Page', '/capital-colours', '#C2185B')}
        </div>`;

        const html = `<div style="font-family:'Segoe UI',sans-serif;padding:4px 2px 30px">
            ${kpis}
            <div style="display:grid;grid-template-columns:1.3fr 1fr;gap:18px">
              <div>${section('📦 Orders to deliver (pending)', so)}</div>
              <div>${section('🎨 Top shades by output', bars)}</div>
            </div>
            ${section('🧪 Recent production', rec)}
            ${section('⚡ Quick actions', quick)}
        </div>`;
        $body.html(html);
    }

    function qbtn(label, href, color) {
        return `<a href="${href}" style="display:inline-block;padding:11px 18px;border-radius:10px;
            background:${color};color:#fff;font-weight:700;text-decoration:none;font-size:13px">${label}</a>`;
    }

    load();
};
