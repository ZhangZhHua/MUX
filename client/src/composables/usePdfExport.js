import { ref } from 'vue';
import html2pdf from 'html2pdf.js';

/**
 * PDF 导出组合式函数
 *
 * 功能说明：
 * - 将实验详情页的所有信息（概览、公告、任务、人员、步骤、附件、日志）导出为 PDF
 * - 日志按日期倒序排列（最新在顶部），放在 PDF 最后
 * - 附件仅显示文件名 + 可访问链接，不嵌入实际内容
 */

export function usePdfExport() {
  const isExporting = ref(false);

  const escapeHtml = (str) => {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&' + 'amp;')
      .replace(/</g, '&' + 'lt;')
      .replace(/>/g, '&' + 'gt;')
      .replace(/"/g, '&' + 'quot;')
      .replace(/'/g, '&' + '#39;');
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  const formatTime = (isoStr) => {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${m}-${day} ${hh}:${mm}`;
  };

  const truncateFileName = (name, max = 30) => {
    if (!name || name.length <= max) return name;
    const ext = name.lastIndexOf('.');
    if (ext > 0) {
      const extension = name.slice(ext);
      const base = name.slice(0, ext);
      return base.slice(0, max - extension.length - 3) + '...' + extension;
    }
    return name.slice(0, max - 3) + '...';
  };

  const buildLogHtml = (log, apiBaseUrl) => {
    const authorName = log.author
      ? `${log.author.first_name || ''} ${log.author.last_name || ''}`.trim()
      : 'Unknown';
    const participants = log.participants || '';
    const time = formatTime(log.shift_date || log.created_at);

    let attachmentLinks = '';
    if (log.attachments && log.attachments.length > 0) {
      attachmentLinks = `
        <div style="margin-top: 6px; font-size: 11px; color: #6b7280;">
          📎 附件：
          ${log.attachments.map(f =>
            `<span style="margin-right: 10px;">${escapeHtml(truncateFileName(f))} <span style="color: #9ca3af;">[${escapeHtml(apiBaseUrl)}/experiments/attachments/${escapeHtml(f)}]</span></span>`
          ).join('')}
        </div>`;
    }

    return `
      <div style="margin-bottom: 14px; padding: 12px; background: #f9fafb; border-radius: 6px; border-left: 3px solid #6366f1;">
        <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">
          <strong>${escapeHtml(authorName)}</strong>
          ${participants ? ' · 操作员：' + escapeHtml(participants) : ''}
          <span style="float: right;">${escapeHtml(time)}</span>
        </div>
        <div style="font-size: 13px; line-height: 1.6; color: #374151; white-space: pre-wrap;">${escapeHtml(log.content)}</div>
        ${attachmentLinks}
      </div>`;
  };

  /**
   * 进行 PDF 导出
   *
   * @param {Object} options
   * @param {Object} options.experiment - 实验对象
   * @param {string} options.descriptionHtml - 已编译的 Markdown HTML
   * @param {Array}  options.bulletins - 公告列表
   * @param {Array}  options.steps - 操作步骤列表
   * @param {Array}  options.groupedLogColumns - 按日期分组的日志列 (已按日期倒序)
   * @param {Array}  options.contributorStats - 贡献排行榜
   * @param {Array}  options.allAttachments - 所有附件扁平列表 [{file, log}]
   * @param {string} options.apiBaseUrl - API 基础 URL
   */
  const exportToPdf = async ({
    experiment,
    descriptionHtml,
    bulletins = [],
    steps = [],
    groupedLogColumns = [],
    contributorStats = [],
    allAttachments = [],
    apiBaseUrl = ''
  }) => {
    if (!experiment) return;

    isExporting.value = true;

    let container = null;

    try {
      const title = escapeHtml(experiment.title || 'Untitled Experiment');
      const status = escapeHtml(experiment.status || 'unknown');
      const statusColor = experiment.status === 'running' ? '#10b981' : experiment.status === 'completed' ? '#6366f1' : '#f59e0b';
      const tags = (experiment.tags || []).map(t => escapeHtml(t.name)).join(', ') || '—';
      const currentTask = experiment.current_task || '—';
      const generatedDate = formatDate(new Date().toISOString());

      // 描述内容（已是 HTML，不转义）
      const descriptionSection = descriptionHtml || '<em>No description recorded.</em>';

      // 公告
      let bulletinsHtml = '';
      if (bulletins.length > 0) {
        bulletinsHtml = bulletins.map(b =>
          `<div style="margin-bottom: 8px; padding: 8px 12px; background: #fef3c7; border-radius: 4px; border-left: 3px solid #f59e0b;">
            <span style="font-size: 11px; color: #92400e;">${escapeHtml(formatTime(b.created_at))} · ${escapeHtml(b.author || '')}</span>
            <div style="font-size: 12px; color: #78350f; margin-top: 2px;">${escapeHtml(b.text || '')}</div>
          </div>`
        ).join('');
      } else {
        bulletinsHtml = '<div style="font-size: 12px; color: #9ca3af; padding: 8px;">暂无公告</div>';
      }

      // 人员
      let personnelHtml = '';
      const members = experiment.members || [];
      if (members.length > 0) {
        personnelHtml = members.map(m =>
          `<span style="display: inline-block; margin: 3px 6px; padding: 4px 10px; background: #e0e7ff; border-radius: 12px; font-size: 12px; color: #3730a3;">${escapeHtml(m.first_name || '')} ${escapeHtml(m.last_name || '')}</span>`
        ).join('');
      } else {
        personnelHtml = '<span style="font-size: 12px; color: #9ca3af;">暂无人员分配</span>';
      }

      // 贡献榜
      let contributorHtml = '';
      if (contributorStats.length > 0) {
        contributorHtml = `
          <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px;">
            <thead>
              <tr style="background: #f3f4f6;">
                <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">#</th>
                <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">姓名</th>
                <th style="padding: 6px 8px; text-align: center; border-bottom: 1px solid #e5e7eb;">操作次数</th>
                <th style="padding: 6px 8px; text-align: center; border-bottom: 1px solid #e5e7eb;">附件数</th>
                <th style="padding: 6px 8px; text-align: center; border-bottom: 1px solid #e5e7eb;">合计</th>
              </tr>
            </thead>
            <tbody>
              ${contributorStats.map((item, i) => `
                <tr style="border-bottom: 1px solid #f3f4f6;">
                  <td style="padding: 5px 8px;">${i + 1}</td>
                  <td style="padding: 5px 8px;">${escapeHtml(item.user?.first_name || '')} ${escapeHtml(item.user?.last_name || '')}</td>
                  <td style="padding: 5px 8px; text-align: center;">${item.logCount || 0}</td>
                  <td style="padding: 5px 8px; text-align: center;">${item.attachmentCount || 0}</td>
                  <td style="padding: 5px 8px; text-align: center; font-weight: bold;">${item.total || 0}</td>
                </tr>`).join('')}
            </tbody>
          </table>`;
      }

      // 步骤
      let stepsHtml = '';
      if (steps.length > 0) {
        stepsHtml = steps.map(s =>
          `<div style="margin-bottom: 4px; padding: 4px 0; font-size: 12px; color: #374151;">
            ${s.is_completed ? '✅' : '⬜'} ${escapeHtml(s.title || '')}
          </div>`
        ).join('');
      } else {
        stepsHtml = '<div style="font-size: 12px; color: #9ca3af;">暂无操作步骤</div>';
      }

      // 附件汇总（只列出文件名和链接）
      let allAttachmentsHtml = '';
      if (allAttachments.length > 0) {
        allAttachmentsHtml = allAttachments.map(item =>
          `<div style="margin-bottom: 3px; font-size: 11px; color: #4b5563;">
            📎 ${escapeHtml(truncateFileName(item.file || ''))}
            <span style="color: #9ca3af;">[${escapeHtml(apiBaseUrl)}/experiments/attachments/${escapeHtml(item.file || '')}]</span>
            <span style="color: #9ca3af; font-size: 10px;">(${escapeHtml(formatDate(item.log?.shift_date || item.log?.created_at))})</span>
          </div>`
        ).join('');
      } else {
        allAttachmentsHtml = '<div style="font-size: 12px; color: #9ca3af;">暂无附件</div>';
      }

      // 日志（按日期倒序，由 groupedLogColumns 保证顺序）
      let logsHtml = '';
      if (groupedLogColumns.length > 0) {
        logsHtml = groupedLogColumns.map(col => {
          const logsForDate = col.logs || [];
          return `
            <div style="margin-bottom: 20px;">
              <div style="font-size: 14px; font-weight: bold; color: #1f2937; padding-bottom: 6px; border-bottom: 2px solid #6366f1; margin-bottom: 10px;">
                📅 ${escapeHtml(col.date || '')} · ${logsForDate.length} 条日志
              </div>
              ${logsForDate.map(log => buildLogHtml(log, apiBaseUrl)).join('')}
            </div>`;
        }).join('');
      } else {
        logsHtml = '<div style="font-size: 13px; color: #9ca3af; text-align: center; padding: 20px;">暂无日志记录</div>';
      }

      // ===== 方案一：全屏可见覆盖层 =====
      // 构建实际要导出的内容（白纸区域）
      const paperContent = `
<div style="width: 794px; padding: 30px 35px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 13px; color: #1f2937; line-height: 1.6; background: #ffffff; box-sizing: border-box; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; text-rendering: optimizeLegibility;">
  <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 3px solid #6366f1;">
    <h1 style="font-size: 22px; color: #111827; margin: 0 0 6px 0;">${title} <span style="display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; color: #fff; margin-left: 8px; background: ${statusColor};">${status}</span></h1>
    <div style="font-size: 12px; color: #6b7280;">标签：${tags} · 导出时间：${generatedDate}</div>
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">详细说明文档</div>
    <div style="font-size: 13px; line-height: 1.8; color: #374151;">${descriptionSection}</div>
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">当前执行任务</div>
    <div style="font-size: 13px; padding: 10px 14px; background: #f0fdf4; border-radius: 6px; border-left: 3px solid #10b981; color: #065f46;">${escapeHtml(currentTask)}</div>
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">实时公告</div>
    ${bulletinsHtml}
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">实验人员</div>
    <div style="margin-bottom: 10px;">${personnelHtml}</div>
    ${contributorHtml}
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">操作步骤清单</div>
    ${stepsHtml}
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">所有附件（文件名 + 链接）</div>
    ${allAttachmentsHtml}
  </div>

  <div style="margin-bottom: 22px;">
    <div style="font-size: 15px; font-weight: 700; color: #374151; margin-bottom: 10px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb;">日志看板（按日期倒序：最新在顶部）</div>
    ${logsHtml}
  </div>

  <div style="margin-top: 30px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 10px; color: #9ca3af; text-align: center;">
    由 MUX 系统自动生成 · ${generatedDate}
  </div>
</div>`;

      // 创建全屏覆盖层
      container = document.createElement('div');
      container.id = 'pdf-export-overlay';
      container.style.cssText =
        'position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 2147483647; background: rgba(0,0,0,0.5); display: flex; flex-direction: column; align-items: center; overflow-y: auto; -webkit-overflow-scrolling: touch;';

      // 状态提示条
      const statusBar = document.createElement('div');
      statusBar.style.cssText =
        'width: 794px; padding: 12px 0; text-align: center; font-size: 13px; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, sans-serif; flex-shrink: 0;';
      statusBar.textContent = '📄 正在生成 PDF，请稍候...';

      // 白纸内容区
      const paper = document.createElement('div');
      paper.style.cssText = 'flex-shrink: 0; margin-bottom: 40px;';
      paper.innerHTML = paperContent;

      container.appendChild(statusBar);
      container.appendChild(paper);
      document.body.appendChild(container);

      // 调试：确认 DOM 已挂载且有内容
      console.log('[PDF Export] Container mounted, content length:', paperContent.length);
      console.log('[PDF Export] Paper dimensions:', paper.offsetWidth, 'x', paper.offsetHeight);

      // 等待浏览器完成布局和渲染
      await new Promise(resolve => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            setTimeout(resolve, 300);
          });
        });
      });

      // 二次确认渲染尺寸
      const renderedW = paper.offsetWidth;
      const renderedH = paper.offsetHeight;
      console.log('[PDF Export] After render - Paper:', renderedW, 'x', renderedH);
      if (renderedW === 0 || renderedH === 0) {
        console.error('[PDF Export] Paper element has zero dimensions! This will cause blank PDF.');
      }

      const safeFilename = (experiment.title || 'experiment')
        .replace(/[\\/:*?"<>|]/g, '_')
        .substring(0, 80);
      const pdfFilename = `${safeFilename}_${generatedDate}.pdf`;

      // 生成 PDF，注意 from() 传入的是 whitePaper 而不是整个覆盖层
      const pdfWorker = html2pdf().set({
        margin: [10, 10, 10, 10],
        filename: pdfFilename,
        image: { type: 'jpeg', quality: 0.82 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff',
          width: 794
        },
        jsPDF: {
          unit: 'mm',
          format: 'a4',
          orientation: 'portrait',
          compress: true
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      });

      // 直接从 paper 元素导出（不含覆盖层半透明背景）
      await pdfWorker.from(paper).save();

      console.log('[PDF Export] Done!');

    } catch (error) {
      console.error('[PDF Export] Failed:', error);
      throw error;
    } finally {
      // 清理全屏覆盖层
      if (container && container.parentNode) {
        document.body.removeChild(container);
      }
      isExporting.value = false;
    }
  };

  return {
    isExporting,
    exportToPdf
  };
}