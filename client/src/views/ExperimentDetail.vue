<template>
  <div class="detail-layout">
    <!-- 1. 全局顶部栏 -->
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />
    <!-- 2. 全局左侧栏 -->
    <Sidebar :groups="userGroups" :currentGroupId="activeGroupId" :isOpen="isSidebarOpen" @group-change="goBackHome" @close="isSidebarOpen = false" />

    <!-- 3. 实验内页主舞台 -->
    <main class="detail-main" v-if="experiment">
      <!-- 实验元信息通栏 (Meta Bar) -->
      <div class="exp-meta-bar">
        <div class="meta-left">
          <button class="btn-back" @click="goBackHome">⬅️ Back to Dashboard</button>
          <div class="title-row">
            <h2>{{ experiment.title }}</h2>
            <span class="status-indicator" :class="experiment.status">
              {{ formatStatusText(experiment.status) }}
            </span>
          </div>
          <div class="meta-tags">
            <span class="hash-tag" v-for="t in experiment.tags" :key="t.id">{{ t.name }}</span>
          </div>
        </div>
        <div class="meta-right" v-if="userRole !== 'member'">
          <button class="btn-edit-meta" @click="openEditMetaModal">⚙️ Edit Experiment Info</button>
          <button class="btn-delete-meta" @click="handleDeleteExperiment">🗑️ Delete Experiment</button>
        </div>
      </div>

      <div class="workspace-split">
        <!-- 【左中画布】流式垂直平铺核心区 -->
        <div class="canvas-center">
          
          <!-- 板块 1：📜 实验详细介绍 (默认折叠以确保值班日志看板迅速触达，支持一键动态拉伸展开) -->
          <div class="content-block collapsed-container">
            <div class="block-header">
              <div class="header-left-meta">
                <h3 class="block-title">📜 1. Detailed Overview Document</h3>
                <span class="collapse-hint-text" @click="isOverviewExpanded = !isOverviewExpanded">
                  {{ isOverviewExpanded ? '▼ Click to hide overview document' : '▶ Click to expand USTC overview document' }}
                </span>
              </div>
              <div class="editor-controls">
                <select v-model="editFormatType" class="format-select" :disabled="isMarkdownMode || !isOverviewExpanded">
                  <option value="markdown">Markdown Mode</option>
                  <option value="text">Plain Text Mode</option>
                </select>
                <button class="btn-toggle-mode" @click="toggleEditMode" :disabled="!isOverviewExpanded">
                  {{ isMarkdownMode ? '✍️ Edit Document' : '👁️ Preview Layout' }}
                </button>
                <button class="btn-expand-trigger" @click="isOverviewExpanded = !isOverviewExpanded">
                  {{ isOverviewExpanded ? '📁 Collapse' : '👁️ Expand' }}
                </button>
              </div>
            </div>
            
            <!-- 带有 Vue 3 slide-fade 丝滑动画过渡的折叠舱 -->
            <transition name="slide-fade">
              <div class="overview-body-drawer" v-if="isOverviewExpanded">
                <!-- 💡 核心修复：在此处补齐 v-if="isMarkdownMode"，使之与下方的 v-else 形成完美的条件编译对齐 -->
                <div class="markdown-view-wrapper" v-if="isMarkdownMode">
                  <div v-if="editFormatType === 'markdown'" class="markdown-body" v-html="compileMarkdown(editDescription)"></div>
                  <pre v-else class="plain-text-body">{{ editDescription || 'No document content recorded.' }}</pre>
                </div>
                
                <div class="editor-body" v-else>
                  <textarea class="static-textarea" rows="10" v-model="editDescription"></textarea>
                  <div class="editor-actions">
                    <button class="btn-cancel-inline" @click="handleCancelEdit">Cancel</button>
                    <button class="btn-save-inline" @click="handleSaveDescription">Save Document</button>
                  </div>
                </div>
              </div>
            </transition>
          </div>

          <!-- 板块 2：📢 实验室置顶通知看板 (亮眼学术橙黄，主管可动态发布/清除通告，全员一目了然) -->
          <div class="content-block bg-notification-board">
            <div class="block-header">
              <h3 class="block-title font-yellow">📢 2. Urgent Live Bulletins & Notices</h3>
              <span class="bulletin-count-badge">{{ bulletins.length }} Notices Active</span>
            </div>
            
            <div class="bulletins-list" v-if="bulletins.length > 0">
              <div v-for="item in bulletins" :key="item.id" class="bulletin-item">
                <span class="bulletin-symbol">💡</span>
                <div class="bulletin-content-wrapper">
                  <p class="bulletin-text">{{ item.text }}</p>
                  <span class="bulletin-author">Posted by {{ item.author }} at {{ formatTimeOnly(item.created_at) }}</span>
                </div>
                <button v-if="userRole !== 'member'" class="btn-delete-bulletin" title="Clear notice" @click="removeBulletin(item.id)">&times;</button>
              </div>
            </div>
            <div class="empty-bulletins" v-else>
              🕊️ No urgent alerts or pinned guidelines active for this experiment workspace.
            </div>

            <div class="bulletin-quick-post" v-if="userRole !== 'member'">
              <input type="text" v-model="newBulletinInput" placeholder="Post a quick urgent notice for today's operators (e.g. SF6 gas check)..." @keydown.enter.prevent="addBulletin" />
              <button class="btn-post-bulletin" @click="addBulletin">Broadcast Notice</button>
            </div>
          </div>

          <!-- 板块 3：⚡ Currently Executing Task (任务面板) -->
          <div class="content-block task-block">
            <div class="block-header">
              <h3 class="block-title font-yellow">⚡ 3. Currently Executing Task</h3>
              <button 
                v-if="canEditCurrentTask && !isEditingCurrentTask" 
                class="btn-add-participant"
                @click="enterTaskEditMode"
              >
                ✍️ Update Task
              </button>
            </div>
            
            <div v-if="!isEditingCurrentTask" class="task-display-content" style="text-align: left; padding: 10px 0;">
              <p v-if="experiment.current_task" class="current-task-text" style="font-size: 13.5px; line-height: 1.5; color: #334155; white-space: pre-wrap; margin: 0;">{{ experiment.current_task }}</p>
              <p v-else class="empty-task-text" style="font-size: 12px; color: #94a3b8; font-style: italic; margin: 0;">💡 No active tasks defined for this workspace currently. Click "Update Task" to define the current executing task.</p>
            </div>
            
            <form v-else @submit.prevent="handleSaveCurrentTask" class="task-edit-form" style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
              <textarea 
                v-model="editCurrentTaskInput" 
                placeholder="Describe what tasks are currently being executed (e.g. calibration of spectrometer, helium level check)..." 
                rows="3" 
                style="width: 100%; border: 1px solid var(--border-color); border-radius: 6px; padding: 8px 12px; font-size: 13px; resize: vertical; outline: none; background: #ffffff; color: #1e293b;"
                required
              ></textarea>
              <div class="task-edit-actions" style="display: flex; gap: 8px; justify-content: flex-end;">
                <button type="button" class="btn-cancel-inline" @click="cancelTaskEdit" style="padding: 6px 12px; font-size: 12px;">Cancel</button>
                <button type="submit" class="btn-save-inline" style="padding: 6px 12px; font-size: 12px;">Save Task</button>
              </div>
            </form>
          </div>

          <!-- 板块 4：📋 每日日志看板 (下移为第四栏) -->
          <div class="content-block no-padding bg-kanban-track">
            <div class="block-header padding-inside" style="display: flex; justify-content: space-between; align-items: center; width: 100%; box-sizing: border-box;">
              <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <h3 class="block-title">📋 4. Daily Log Kanban</h3>
                <span class="kanban-tip">Logs auto-grouped by shift date ➔</span>
              </div>
              <button class="btn-record-log" @click="openAddLogModal(null)">
                <span>➕ Record Daily Log</span>
              </button>
            </div>
            
            <div class="kanban-scroll-row" v-if="groupedColumns.length > 0">
              <div v-for="col in groupedColumns" :key="col.date" class="kanban-column">
                <div class="col-header">
                  <h4>
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 6px; color: #64748b;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    {{ col.date }}
                  </h4>
                  <button class="btn-add-log-inline" @click="openAddLogModal(col.logs[0].shift_date)">+</button>
                </div>
                
                <div class="cards-stack">
                  <div v-for="log in getDisplayedLogs(col)" :key="log.id" class="log-card">
                    <div class="log-card-meta">
                      <span class="logger-name">
                        <img v-if="log.author?.avatar_node" :src="getAvatarUrl(log.author.avatar_node)" class="log-author-avatar-img" />
                        <span v-else>👤</span>
                        {{ log.author?.first_name }} {{ log.author?.last_name }}
                      </span>
                      <span class="log-time">{{ formatTimeOnly(log.created_at) }}</span>
                    </div>
                    <p class="log-text">{{ log.content.length > 110 ? log.content.slice(0, 110) + '...' : log.content }}</p>
                    
                    <div class="card-action-row">
                      <button class="btn-read-more" @click="openLogDetails(log)">View & Edit Details ➔</button>
                    </div>

                    <div class="log-participants" v-if="log.participants">
                      👥 Operators: {{ log.participants }}
                    </div>
                    
                    <!-- 真实多附件渲染 -->
                    <div class="log-card-attachments" v-if="log.attachments && log.attachments.length > 0">
                      <div v-for="file in log.attachments" :key="file" class="card-attach-chip" :title="file">
                        <a href="#" @click.prevent="handleAttachmentClick(file, log.author ? `${log.author.first_name} ${log.author.last_name}` : 'Unknown', `Shift Date: ${col.date}`)" class="card-attach-clickable">
                          📎 {{ truncateFileName(file, 16) }}
                        </a>
                        <button 
                          v-if="file.toLowerCase().endsWith('.pdf')" 
                          class="btn-preview-attachment" 
                          title="Preview PDF online"
                          @click.stop.prevent="triggerPdfPreview(file)"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Show More / Less button for column logs -->
                <button 
                  v-if="col.logs.length > KANBAN_LOG_LIMIT" 
                  class="btn-toggle-expand" 
                  @click="toggleDateExpansion(col.date)"
                  style="margin-top: 10px; width: 100%; border-style: dashed;"
                >
                  {{ isDateExpanded(col.date) ? 'Show Less 🔼' : `Show More (${col.logs.length - KANBAN_LOG_LIMIT} more) 🔽` }}
                </button>
              </div>
            </div>

            <div class="empty-kanban-state" v-else>
              <p>📭 No operational logs recorded for this shift sequence yet.</p>
              <button class="btn-add-first-log" @click="openAddLogModal()">+ Record First Shift Log</button>
            </div>
          </div>

          <div class="content-block" style="margin-top: 20px;">
            <div class="block-header">
              <h3 class="block-title">👥 5. Experiment Assigned Personnel</h3>
              <button class="btn-add-participant" v-if="userRole !== 'member'" @click="openManagePersonnelModal">
                ⚙️ Manage Personnel
              </button>
            </div>
            
            <div class="participants-list-row" v-if="experiment.members && experiment.members.length > 0">
              <div class="participant-chip" v-for="user in experiment.members" :key="user.id">
                <img v-if="user.avatar_node" :src="getAvatarUrl(user.avatar_node)" class="p-avatar-img" />
                <span v-else class="p-avatar">👤</span>
                <div class="p-info">
                  <span class="p-name">{{ user.first_name }} {{ user.last_name }}</span>
                  <span class="p-role">{{ user.role.toUpperCase() }}</span>
                </div>
              </div>
            </div>
            
            <div class="contribution-stats-box" v-if="contributorStats.length > 0" style="margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
              <h4 style="font-size: 13.5px; color: #475569; margin: 0 0 12px 0; text-align: left; display: flex; align-items: center; gap: 6px; font-weight: 600;">
                <span>📊  Contribution Leaderboard</span>
                <span class="info-tooltip-container" style="position: relative; display: inline-flex; align-items: center;">
                  <span class="info-tooltip-trigger" style="cursor: pointer; color: #94a3b8; font-size: 11px; display: inline-flex; align-items: center; justify-content: center; width: 14px; height: 14px; border: 1px solid #cbd5e1; border-radius: 50%; font-family: monospace; font-weight: bold; line-height: 1; user-select: none;">!</span>
                  <span class="info-tooltip-content" style="visibility: hidden; opacity: 0; position: absolute; bottom: 125%; left: 50%; transform: translateX(-50%); width: 300px; background-color: #1e293b; color: #fff; text-align: left; border-radius: 6px; padding: 10px; font-size: 12px; font-weight: 500; line-height: 1.4; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); z-index: 10; transition: opacity 0.15s ease, visibility 0.15s ease; pointer-events: none;">
                    <strong style="color: #38bdf8; display: block; margin-bottom: 4px;">Sorting Rule:</strong>
                    Ranked by (ops + atts) descending.<br/>
                    • <span style="color: #38bdf8; font-weight: bold;">ops</span>: Logs participated as active Operator.<br/>
                    • <span style="color: #c084fc; font-weight: bold;">atts</span>: Attachments uploaded by this researcher.
                    <span style="position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border-width: 5px; border-style: solid; border-color: #1e293b transparent transparent transparent;"></span>
                  </span>
                </span>
              </h4>
              <div class="stats-tree-list" style="display: flex; flex-direction: column; gap: 6px; text-align: left; max-width: 480px;">
                <div class="stat-tree-node" v-for="(item, index) in contributorStats" :key="item.user.id" style="display: flex; align-items: center; justify-content: space-between; padding: 4px 0; position: relative;">
                  <div style="display: flex; align-items: center; gap: 4px;">
                    <span style="font-family: monospace; color: #cbd5e1; font-weight: bold; font-size: 13px; margin-right: 6px; letter-spacing: -1px; user-select: none;">
                      {{ index === contributorStats.length - 1 ? '└──' : '├──' }}
                    </span>
                    <span :style="{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      fontSize: '11px',
                      fontWeight: '700',
                      marginRight: '6px',
                      fontFamily: 'monospace',
                      background: index === 0 ? '#fef3c7' : (index === 1 ? '#e2e8f0' : (index === 2 ? '#ffedd5' : '#f1f5f9')),
                      color: index === 0 ? '#b45309' : (index === 1 ? '#475569' : (index === 2 ? '#c2410c' : '#64748b'))
                    }">
                      {{ index + 1 }}
                    </span>
                    <img v-if="item.user.avatar_node" :src="getAvatarUrl(item.user.avatar_node)" style="width: 22px; height: 22px; border-radius: 50%; object-fit: cover; border: 1px solid #cbd5e1; margin-right: 4px;" />
                    <span v-else style="font-size: 14px; margin-right: 4px;">👤</span>
                    <span style="font-size: 12.5px; font-weight: 600; color: #334155;">{{ item.user.first_name }} {{ item.user.last_name }}</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <span title="Logs participated as Operator" style="background: #e0f2fe; color: #0369a1; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-family: monospace;">
                      📝 {{ item.logCount }} ops
                    </span>
                    <span title="Attachments Uploaded" style="background: #f3e8ff; color: #6b21a8; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-family: monospace;">
                      📎 {{ item.attachmentCount }} atts
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div class="empty-personnel-tip" v-if="!experiment.members || experiment.members.length === 0">
              💡 No specific personnel assigned. Click "Manage Personnel" to add members from your research team.
            </div>
          </div>

        </div>

        <!-- 右侧辅助面板（全量附件总览与追溯控制台） -->
        <div class="utility-dock">
          <!-- 📋 Experimental Operational Steps Checklist -->
          <div class="dock-panel steps-panel" style="margin-bottom: 20px;">
            <div class="panel-title-row" style="display: flex; justify-content: space-between; align-items: center;">
              <h3>📋 Operational Steps</h3>
              <button 
                v-if="userRole !== 'member'" 
                class="btn-add-participant" 
                style="padding: 2px 8px; font-size: 11px;"
                @click="showManageStepsModal = true"
              >
                ⚙️ Manage
              </button>
            </div>
            
            <div class="steps-list" v-if="stepsList.length > 0" style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px; text-align: left;">
              <div v-for="step in stepsList" :key="step.id" class="step-item" style="display: flex; align-items: flex-start; gap: 8px;">
                <input 
                  type="checkbox" 
                  :checked="step.is_completed" 
                  @change="toggleStepCompletion(step)" 
                  style="margin-top: 3px; cursor: pointer;"
                />
                <span :style="{ textDecoration: step.is_completed ? 'line-through' : 'none', color: step.is_completed ? '#94a3b8' : '#334155', fontSize: '13px' }">
                  {{ step.title }}
                </span>
              </div>
            </div>
            <div v-else style="font-size: 12px; color: #94a3b8; text-align: left; margin-top: 12px;">
              📝 No operation steps defined.
            </div>
          </div>

          <div class="dock-panel">
            <div class="panel-title-row"><h3>📎 All Experiment Attachments</h3></div>
            <div class="task-list">
              <div v-for="item in displayedAttachments" :key="item.file" class="task-item">
                <div class="task-main">
                  <!-- 物理点击安全预览或下载 -->
                  <span class="task-name" @click="handleAttachmentClick(item.file, item.log.author ? `${item.log.author.first_name} ${item.log.author.last_name}` : 'Unknown', `Log ID: #${item.log.id}`)" style="color:var(--primary-color); font-weight:600; cursor:pointer;" :title="item.file">
                    {{ truncateFileName(item.file, 22) }}
                  </span>
                  <span class="task-deadline">By {{ item.log.author?.first_name }}</span>
                </div>
                <div class="task-action-wrapper" style="display: flex; gap: 8px; align-items: center;">
                  <button 
                    v-if="item.file.toLowerCase().endsWith('.pdf')" 
                    class="btn-preview-attachment-tiny" 
                    title="Preview PDF" 
                    @click.stop.prevent="triggerPdfPreview(item.file)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  </button>
                  <span class="task-status verified" style="cursor:pointer;" @click="openLogDetails(item.log)">Trace</span>
                </div>
              </div>
              <div v-if="allFlattenedAttachments.length === 0" class="file-info" style="text-align:left;">No files uploaded.</div>
              
              <!-- Expand / Collapse control -->
              <button 
                v-if="allFlattenedAttachments.length > ATTACHMENTS_LIMIT" 
                class="btn-toggle-expand" 
                @click="isAttachmentsExpanded = !isAttachmentsExpanded"
              >
                {{ isAttachmentsExpanded ? 'Show Less 🔼' : `Show More (${allFlattenedAttachments.length - ATTACHMENTS_LIMIT} more) 🔽` }}
              </button>
            </div>
          </div>

          <!-- 🖼️ Image Gallery Panel -->
          <div class="dock-panel image-gallery-panel" style="margin-top: 20px;">
            <div class="panel-title-row" style="display: flex; justify-content: space-between; align-items: center;">
              <h3>🖼️ Image Gallery <span class="gallery-count-badge">{{ allFlattenedImages.length }}</span></h3>
            </div>
            <div class="image-gallery-grid" v-if="displayedImages.length > 0">
              <div 
                v-for="item in displayedImages" 
                :key="item.file" 
                class="gallery-item-card"
                @click="handleAttachmentClick(item.file, item.log.author ? `${item.log.author.first_name} ${item.log.author.last_name}` : 'Unknown', `Log ID: #${item.log.id}`)"
                :title="`${item.file} (Uploaded by ${item.log.author?.first_name || 'Unknown'})`"
              >
                <img :src="getImageStreamUrl(item.file)" class="gallery-thumb-img" alt="Thumbnail" />
              </div>
            </div>
            <div v-else class="file-info" style="text-align: left; padding: 8px 0;">No images captured.</div>

            <!-- Expand / Collapse control -->
            <button 
              v-if="allFlattenedImages.length > GALLERY_LIMIT" 
              class="btn-toggle-expand" 
              @click="isGalleryExpanded = !isGalleryExpanded"
            >
              {{ isGalleryExpanded ? 'Show Less 🔼' : `Show More (${allFlattenedImages.length - GALLERY_LIMIT} more) 🔽` }}
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- 弹窗 A：完全体详情与修改一体化弹窗 -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showLogDetailModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeLogModal()">
        <div class="modal-box log-detail-modal">
          <div class="modal-header">
            <h3>Shift Log Node</h3>
            <button class="btn-close-x" @click="closeLogModal">&times;</button>
          </div>
          
          <!-- 状态一：标准阅读模式 -->
          <div v-if="!isLogEditingFlow">
            <p class="modal-subtitle" style="text-align:left; margin-bottom:12px;">
              Recorded by <strong>{{ selectedLog?.author?.first_name }} {{ selectedLog?.author?.last_name }}</strong>
            </p>
            <div class="modal-log-content">
              <p class="full-log-paragraph">{{ selectedLog?.content }}</p>
            </div>
            <div class="modal-log-footer">
              <div class="footer-meta-item" v-if="selectedLog?.participants"><strong>Operators:</strong> <span class="footer-badge">{{ selectedLog?.participants }}</span></div>
              
              <!-- 多附件展示 -->
              <div class="footer-meta-item" v-if="selectedLog?.attachments && selectedLog.attachments.length > 0">
                <strong>Attachments ({{ selectedLog.attachments.length }}):</strong> 
                <div class="modal-attachment-list">
                  <div v-for="file in selectedLog.attachments" :key="file" class="modal-file-row">
                    <a href="#" @click.prevent="handleAttachmentClick(file, selectedLog.author ? `${selectedLog.author.first_name} ${selectedLog.author.last_name}` : 'Unknown', `Log ID: #${selectedLog.id}`)" class="footer-attach-link-active" :title="file">
                      📎 {{ truncateFileName(file, 26) }}
                    </a>
                    <button 
                      v-if="file.toLowerCase().endsWith('.pdf')" 
                      class="btn-preview-attachment-modal" 
                      title="Preview PDF online"
                      @click.stop.prevent="triggerPdfPreview(file)"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg> Preview
                    </button>
                  </div>
                </div>
              </div>
              
              <div class="modal-edit-action-row">
                <button type="button" class="btn-inline-add" @click.stop.prevent="enterLogEditMode">✍️ Edit This Log Content & Files</button>
              </div>
            </div>
          </div>

          <!-- 状态二：就地动态编辑模式 -->
          <form @submit.prevent="handleSaveLogEdit" class="modal-form-flow" v-else>
            <div class="modal-form-group">
              <label>Modify Log Content *</label>
              <textarea v-model="editLogContent" required rows="5"></textarea>
            </div>
            
            <div class="modal-form-group">
              <label>Select Operators</label>
              <div class="team-checkbox-matrix">
                <div v-for="user in experiment?.members" :key="user.id" class="matrix-item">
                  <input type="checkbox" :id="'edit-log-user-'+user.id" :value="user.first_name + ' ' + user.last_name" v-model="editLogOperators" />
                  <label :for="'edit-log-user-'+user.id">{{ user.first_name }} {{ user.last_name }}</label>
                </div>
              </div>
            </div>
            
            <!-- 编辑状态：多附件自主剔除与追加 -->
            <div class="modal-form-group">
              <label>Manage Log Attachments</label>
              <!-- 附件多磁吸标签列 -->
              <div class="form-files-list" v-if="editLogAttachments.length > 0">
                <div v-for="file in editLogAttachments" :key="file" class="form-file-chip" :title="file">
                  <span>{{ truncateFileName(file, 20) }}</span>
                  <button type="button" class="btn-delete-chip" @click="removeFileFromEdit(file)">&times;</button>
                </div>
              </div>
              
              <!-- 物理追加多附件入口 -->
              <div class="file-uploader-box">
                <input type="file" multiple @change="handleEditFileSelection" class="file-native-input" />
              </div>
            </div>
            
            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="isLogEditingFlow = false">Back</button>
              <button type="submit" class="btn-submit">Save Modifications</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- 弹窗 B：新建日志弹窗 (支持多附件挂载) -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showAddLogModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeAddLogModal()">
        <div class="modal-box log-detail-modal">
          <div class="modal-header">
            <div>
              <h3>Record New Shift Operational Log</h3>
              <p class="modal-subtitle" style="text-align:left; color: #64748b; font-weight: 500; margin-top: 4px;">
                Select shift date and enter beam configurations
              </p>
            </div>
            <button class="btn-close-x" @click="closeAddLogModal">&times;</button>
          </div>
          <form @submit.prevent="submitNewLog" class="modal-form-flow">
            <div class="modal-form-group">
              <label>Shift / Operational Date *</label>
              <input type="date" v-model="addLogDateInput" required class="form-input-date" />
            </div>

            <div class="modal-form-group">
              <label>Log Content / Telemetry Records *</label>
              <textarea v-model="newLogContent" required rows="5" placeholder="Describe current beam state, cryostat configurations..."></textarea>
            </div>

            <div class="modal-form-group">
              <label>Select Active Operators for this Shift</label>
              <div class="team-checkbox-matrix" v-if="experiment?.members && experiment.members.length > 0">
                <div v-for="user in experiment.members" :key="user.id" class="matrix-item">
                  <input type="checkbox" :id="'log-user-'+user.id" :value="user.first_name + ' ' + user.last_name" v-model="selectedLogOperators" />
                  <label :for="'log-user-'+user.id">{{ user.first_name }} {{ user.last_name }}</label>
                </div>
              </div>
              <div class="empty-matrix-fallback" v-else>⚠️ Assign personnel to the experiment first to select operators.</div>
            </div>

            <div class="modal-form-group">
              <label>Attach Data Telemetry Files (Multi-selectable)</label>
              <div class="file-uploader-box" style="flex-direction: column; align-items: flex-start;">
                <input type="file" multiple @change="handleNewLogFileSelection" />
                
                <!-- 已确认上传的小药丸 -->
                <div class="form-files-list" v-if="uploadedFileNames.length > 0" style="margin-top: 10px; width: 100%;">
                  <div v-for="file in uploadedFileNames" :key="file" class="form-file-chip" :title="file">
                    <span>{{ truncateFileName(file, 20) }}</span>
                    <button type="button" class="btn-delete-chip" @click="removeFileFromNew(file)">&times;</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeAddLogModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="selectedLogOperators.length === 0">Commit Log</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- 弹窗 C：科研团队成员连带关系分配看板 -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showPersonnelModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closePersonnelModal()">
        <div class="modal-box log-detail-modal">
          <div class="modal-header">
            <h3>Manage Experiment Personnel</h3>
            <button class="btn-close-x" @click="closePersonnelModal">&times;</button>
          </div>
          <p class="modal-section-desc">Select members from the main research team to assign to this specific experiment.</p>
          <div class="team-checkbox-matrix large-pool">
            <div v-for="user in allTeamMembers" :key="user.id" class="matrix-item border-style">
              <input type="checkbox" :id="'team-user-'+user.id" :value="user.id" v-model="checkedPersonnelIds" />
              <label :for="'team-user-'+user.id"><strong>{{ user.first_name }} {{ user.last_name }}</strong> ({{ user.email }})</label>
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-cancel" @click="closePersonnelModal">Cancel</button>
            <button type="button" class="btn-submit" @click="handleSavePersonnel">Save Roster</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 弹窗 D：实验元信息全量配置与属性校准面板 -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showEditMetaModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeEditMetaModal()">
        <div class="modal-box log-detail-modal">
          <div class="modal-header">
            <h3>Modify Experiment Meta Details</h3>
            <button class="btn-close-x" @click="closeEditMetaModal">&times;</button>
          </div>
          <form @submit.prevent="handleSaveMetaEdit" class="modal-form-flow">
            <div class="modal-form-group">
              <label>Experiment Title *</label>
              <input type="text" v-model="editMetaTitle" required placeholder="Change experiment title..." />
            </div>

            <div class="modal-form-group">
              <label>Experiment Workspace Status</label>
              <select v-model="editMetaStatus" class="format-select-full">
                <option value="running">🟢 Running (进行中)</option>
                <option value="paused">🟡 Paused (已暂停)</option>
                <option value="stopped">🔴 Stopped (已停止)</option>
                <option value="archived">⚪ Archived (已归档)</option>
              </select>
            </div>

            <div class="modal-form-group">
              <label>Associated Tags (Comma-separated)</label>
              <input type="text" v-model="editMetaTagsInput" placeholder="e.g. #Hardware, #USTC, #Calibration" />
              <small class="form-tip">Separate multi-tags with English commas. System auto-registers new tags if missing.</small>
            </div>

            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeEditMetaModal">Cancel</button>
              <button type="submit" class="btn-submit">Preserve Meta Changes</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- 弹窗 E：实验操作步骤（Checklist）全量管理看板 -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showManageStepsModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeManageStepsModal()">
        <div class="modal-box log-detail-modal" style="max-width: 460px;">
          <div class="modal-header">
            <h3>Manage Experiment Steps</h3>
            <button class="btn-close-x" @click="closeManageStepsModal">&times;</button>
          </div>
          
          <div class="manage-steps-body" style="text-align:left; display:flex; flex-direction:column; gap:14px; margin-top:10px;">
            <!-- List existing steps with Edit/Delete -->
            <div class="existing-steps-list" style="max-height: 250px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;">
              <div v-for="step in stepsList" :key="step.id" class="manage-step-item" style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                <input 
                  type="text" 
                  v-model="step.title" 
                  @change="updateStepTitle(step)"
                  style="border: none; background: transparent; font-size: 13.5px; width: 80%; outline: none;"
                />
                <button 
                  class="btn-delete-step" 
                  @click="deleteStep(step.id)" 
                  style="border: none; background: transparent; color: #ef4444; cursor: pointer; font-size: 14px;"
                >
                  🗑️
                </button>
              </div>
            </div>

            <!-- Form to add new step -->
            <form @submit.prevent="addNewStep" style="display: flex; gap: 8px; margin-top: 10px;">
              <input 
                type="text" 
                v-model="newStepTitleInput" 
                placeholder="Add new step (e.g. Turn on cryogenic pump)..." 
                style="flex: 1; padding: 8px 12px; font-size: 13px; border: 1px solid #cbd5e1; border-radius: 6px; outline:none;"
              />
              <button 
                type="submit" 
                class="btn-submit" 
                style="padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 13.5px; font-weight: 600; cursor: pointer;"
              >
                Add
              </button>
            </form>
          </div>
          
          <div class="modal-actions" style="display: flex; justify-content: flex-end; margin-top: 16px;">
            <button class="btn-submit" @click="closeManageStepsModal">Done</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Teleport C: PDF Preview Overlay Modal -->
    <Teleport to="body">
      <div class="modal-backdrop pdf-preview-backdrop" v-if="isPreviewOpen" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closePdfPreview()">
        <div class="pdf-preview-box">
          <div class="pdf-preview-header">
            <h3>📄 Document Preview: {{ truncateFileName(previewFilename, 45) }}</h3>
            <div class="pdf-header-actions">
              <button class="btn-download-pdf-preview" @click="handleDownloadFile(previewFilename)">⬇️ Download</button>
              <button class="btn-close-pdf-preview" @click="closePdfPreview">&times;</button>
            </div>
          </div>
          <div class="pdf-preview-body">
            <iframe :src="pdfStreamUrl" class="pdf-iframe-element"></iframe>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Teleport D: Image Lightbox Preview -->
    <ImageLightbox 
      :isOpen="isLightboxOpen" 
      :imageUrl="lightboxImageUrl" 
      :filename="lightboxFilename" 
      :uploader="lightboxUploader" 
      :logContext="lightboxContext" 
      @close="closeImageLightbox" 
      @download="handleDownloadFile"
    />

  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../services/api';
import { useToast } from '../composables/useToast';
import Header from '../components/layout/Header.vue';
import Sidebar from '../components/layout/Sidebar.vue';
import ImageLightbox from '../components/common/ImageLightbox.vue';
import { useConfirmDialog } from '../composables/useConfirmDialog';

const router = useRouter();
const route = useRoute();
const toast = useToast();
const { confirm } = useConfirmDialog();

const userName = ref('');
const userRole = ref('');
const userGroups = ref([]);
const activeGroupId = ref(Number(localStorage.getItem('activeGroupId') || 0));
const isSidebarOpen = ref(false);

const experiment = ref(null);
const rawLogs = ref([]);

// Lightbox state variables
const isLightboxOpen = ref(false);
const lightboxImageUrl = ref('');
const lightboxFilename = ref('');
const lightboxUploader = ref('');
const lightboxContext = ref('');

// Expandable lists states
const isAttachmentsExpanded = ref(false);
const isGalleryExpanded = ref(false);
const ATTACHMENTS_LIMIT = 5;
const GALLERY_LIMIT = 8;

// Currently executing task states
const isEditingCurrentTask = ref(false);
const editCurrentTaskInput = ref('');

// Kanban columns logs limit states
const expandedDates = ref(new Set());
const KANBAN_LOG_LIMIT = 3;

// 第一栏实验详细大纲：折叠与展开状态，默认设为折叠 (false)
const isOverviewExpanded = ref(false);
const isMarkdownMode = ref(true);

const editDescription = ref('');
const editFormatType = ref('markdown');

const showLogDetailModal = ref(false);
const showAddLogModal = ref(false);
const showPersonnelModal = ref(false);
const addLogSelectedDate = ref(null);
const addLogDateInput = ref('');

let mouseDownTarget = null;

// Checklist steps refs
const stepsList = ref([]);
const showManageStepsModal = ref(false);
const newStepTitleInput = ref('');

// 实验元信息编辑舱专用 Ref 控制变量
const showEditMetaModal = ref(false);
const editMetaTitle = ref('');
const editMetaStatus = ref('running');
const editMetaTagsInput = ref('');

// 第二栏实验室置顶通知栏数据源 (预设 2 条物理 RPC 实验室常见公告)
const bulletins = ref([]);
const newBulletinInput = ref('');
// 🆕 2. 向后端拉取本实验底下的所有物理置顶通知
const fetchAllBulletins = async () => {
  try {
    const response = await api.get(`/experiments/${experimentId}/bulletins`);
    bulletins.value = response.data;
  } catch (error) {
    console.error("Failed to fetch lab bulletins.");
  }
};

// 🆕 3. 改写发布逻辑：真实的物理网络请求 POST
const addBulletin = async () => {
  if (!newBulletinInput.value.trim()) return;
  try {
    await api.post(`/experiments/${experimentId}/bulletins`, {
      text: newBulletinInput.value.trim()
    });
    newBulletinInput.value = '';
    toast.success("New urgent bulletin broadcasted to database!");
    await fetchAllBulletins(); // 刷新列表，数据流闭环
  } catch (error) {
    toast.error("Failed to broadcast database bulletin.");
  }
};

// 🆕 4. 改写删除逻辑：真实的物理网络请求 DELETE
const removeBulletin = async (bulletinId) => {
  try {
    await api.delete(`/experiments/bulletins/${bulletinId}`);
    toast.success("Notice safely archived from workspace disk.");
    await fetchAllBulletins(); // 刷新列表
  } catch (error) {
    toast.error("Failed to archive bulletin.");
  }
};

const selectedLog = ref(null);
const newLogContent = ref('');
const selectedLogOperators = ref([]);

// 动态多附件物理数组
const uploadedFileNames = ref([]); 

// 日志修改状态机
const isLogEditingFlow = ref(false);
const editLogContent = ref('');
const editLogOperators = ref([]);
const editLogAttachments = ref([]);

const allTeamMembers = ref([]);
const checkedPersonnelIds = ref([]);
const experimentId = route.params.id;

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher';
  userRole.value = localStorage.getItem('role') || 'member';
  await fetchExperimentMeta();
  await fetchAllLogs();
  await fetchUserGroups();
  await fetchAllBulletins();
  await fetchExperimentSteps();
});

const fetchExperimentSteps = async () => {
  try {
    const response = await api.get(`/experiments/${experimentId}/steps`);
    stepsList.value = response.data;
  } catch (error) {
    console.error("Failed to load experiment steps:", error);
  }
};

const addNewStep = async () => {
  const title = newStepTitleInput.value.trim();
  if (!title) return;
  try {
    const response = await api.post(`/experiments/${experimentId}/steps`, { title });
    stepsList.value.push(response.data);
    newStepTitleInput.value = '';
    toast.success("New operational step added!");
  } catch (error) {
    toast.error("Failed to add operational step.");
  }
};

const updateStepTitle = async (step) => {
  const title = step.title.trim();
  if (!title) return;
  try {
    await api.put(`/experiments/${experimentId}/steps/${step.id}`, { title });
    toast.success("Step title updated!");
  } catch (error) {
    toast.error("Failed to update step title.");
    await fetchExperimentSteps(); // Revert on failure
  }
};

const toggleStepCompletion = async (step) => {
  try {
    const newVal = !step.is_completed;
    const response = await api.put(`/experiments/${experimentId}/steps/${step.id}`, {
      is_completed: newVal
    });
    step.is_completed = response.data.is_completed;
    toast.success(newVal ? "Step completed!" : "Step completion canceled.");
  } catch (error) {
    toast.error("Failed to update step status.");
  }
};

const deleteStep = async (stepId) => {
  try {
    await api.delete(`/experiments/${experimentId}/steps/${stepId}`);
    stepsList.value = stepsList.value.filter(s => s.id !== stepId);
    toast.success("Step deleted.");
  } catch (error) {
    toast.error("Failed to delete step.");
  }
};

const closeManageStepsModal = () => {
  showManageStepsModal.value = false;
  newStepTitleInput.value = '';
};

const fetchExperimentMeta = async () => {
  try {
    const response = await api.get(`/experiments/${experimentId}`);
    experiment.value = response.data;
    activeGroupId.value = response.data.group_id;
    editDescription.value = response.data.description || '';
    editFormatType.value = response.data.format_type;
    
    editMetaTitle.value = response.data.title;
    editMetaStatus.value = response.data.status || 'running';
    editMetaTagsInput.value = response.data.tags ? response.data.tags.map(t => t.name).join(', ') : '';
  } catch (error) {
    toast.error("Failed to load experiment specs.");
  }
};

const fetchAllLogs = async () => {
  try {
    const response = await api.get(`/experiments/${experimentId}/logs`);
    rawLogs.value = response.data;
  } catch (error) {
    toast.error("Failed to sync log stream.");
  }
};

// 修复后的 ExperimentDetail.vue 对应函数
const fetchUserGroups = async () => {
  try {
    const response = await api.get('/auth/groups');
    userGroups.value = response.data;
    // 💡 详情页只需要静静加载群组供 Sidebar 下拉框渲染即可，不需要在此处覆写 activeGroupId，也不需要调用 fetchExperiments()
  } catch (error) {
    console.error("Failed to load side clusters registry.");
  }
};

const openEditMetaModal = () => {
  editMetaTitle.value = experiment.value.title;
  editMetaStatus.value = experiment.value.status || 'running';
  editMetaTagsInput.value = experiment.value.tags ? experiment.value.tags.map(t => t.name).join(', ') : '';
  showEditMetaModal.value = true;
};

const closeEditMetaModal = () => {
  showEditMetaModal.value = false;
};

const handleSaveMetaEdit = async () => {
  if (!editMetaTitle.value.trim()) {
    toast.error("Experiment title cannot be empty!");
    return;
  }
  
  const tagsArray = editMetaTagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t.length > 0);

  try {
    const response = await api.put(`/experiments/${experimentId}`, {
      title: editMetaTitle.value.trim(),
      status: editMetaStatus.value,
      tags: tagsArray
    });
    
    experiment.value.title = response.data.title;
    experiment.value.status = response.data.status;
    experiment.value.tags = response.data.tags;
    
    closeEditMetaModal();
    toast.success("Experiment specifications updated smoothly!");
  } catch (error) {
    toast.error(error.response?.data?.detail || "Failed to preserve configuration.");
  }
};

const formatStatusText = (status) => {
  const map = {
    running: '🟢 Running (进行中)',
    paused: '🟡 Paused (已暂停)',
    stopped: '🔴 Stopped (已停止)',
    archived: '⚪ Archived (已归档)'
  };
  return map[status] || '🟢 Running (运行中)';
};

const truncateFileName = (name, maxLen = 18) => {
  if (!name || name.length <= maxLen) return name;
  const extIdx = name.lastIndexOf('.');
  if (extIdx === -1) return name.slice(0, maxLen - 3) + '...';
  const ext = name.slice(extIdx);
  const base = name.slice(0, extIdx);
  const keepLength = maxLen - ext.length - 3;
  if (keepLength <= 0) return name.slice(0, maxLen - 3) + '...';
  return base.slice(0, keepLength) + '...' + ext;
};

const compileMarkdown = (text) => {
  if (!text) return '<em>No document description recorded.</em>';
  const lines = text.split('\n');
  const processedLines = lines.map(line => {
    const trimmed = line.trim();
    if (trimmed === '---') return '<hr style="border:0; height:1px; background:var(--border-color); margin:18px 0;">';
    if (trimmed.startsWith('## ')) return `<h4 style="margin:22px 0 12px 0; font-size:16px; font-weight:700; color:var(--text-main); border-left:3px solid var(--primary-color); padding-left:8px;">${trimmed.replace('## ', '')}</h4>`;
    if (trimmed.startsWith('### ')) return `<h5 style="margin:16px 0 8px 0; font-size:14px; font-weight:600; color:var(--text-main);">${trimmed.replace('### ', '')}</h5>`;
    if (trimmed.startsWith('> ') || trimmed.startsWith('💡 ')) return `<blockquote style="background:#fffdf5; border-left:4px solid #d97706; padding:10px 14px; margin:12px 0; font-size:13px; color:#78350f; border-radius:4px;">${trimmed.replace(/^> |^💡 /, '')}</blockquote>`;
    if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      let core = trimmed.substring(2);
      core = core.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>');
      return `<li style="font-size:13.5px; color:#334155; line-height:1.6; margin-bottom:4px; list-style-type: disc; margin-left: 15px;">${core}</li>`;
    }
    let inlineText = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>');
    return inlineText ? `<p style="font-size:13.5px; line-height:1.6; margin:0 0 6px 0; color:#334155;">${inlineText}</p>` : '';
  });
  return processedLines.join('');
};

const toggleEditMode = () => {
  isMarkdownMode.value = !isMarkdownMode.value;
};

const handleCancelEdit = () => {
  editDescription.value = experiment.value.description || '';
  editFormatType.value = experiment.value.format_type;
  isMarkdownMode.value = true;
};

const handleSaveDescription = async () => {
  try {
    const response = await api.put(`/experiments/${experimentId}`, {
      description: editDescription.value,
      format_type: editFormatType.value
    });
    experiment.value.description = response.data.description;
    experiment.value.format_type = response.data.format_type;
    isMarkdownMode.value = true;
    toast.success("USTC Lab document compiled and deployed!");
  } catch (error) {
    toast.error("Failed to compile content.");
  }
};

const handleNewLogFileSelection = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (uploadedFileNames.value.includes(file.name)) continue;
    
    // Check file size: 50MB limit
    const MAX_SIZE = 50 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      toast.error(`File [${truncateFileName(file.name)}] exceeds the 50MB size limit.`);
      continue;
    }
    
    toast.info(`📤 Uploading file: [${truncateFileName(file.name)}]...`);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await api.post('/experiments/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      uploadedFileNames.value.push(response.data.filename);
      toast.success(`✅ [${truncateFileName(file.name)}] committed to storage node!`);
    } catch (error) {
      toast.error(`Failed to upload [${truncateFileName(file.name)}]`);
    }
  }
  event.target.value = '';
};

const removeFileFromNew = (filename) => {
  uploadedFileNames.value = uploadedFileNames.value.filter(name => name !== filename);
  toast.success(`Removed [${truncateFileName(filename)}] from select stack.`);
};

const submitNewLog = async () => {
  try {
    let logShiftDate = null;
    if (addLogDateInput.value) {
      const parts = addLogDateInput.value.split('-');
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      
      const now = new Date();
      const targetDate = new Date(
        year,
        month,
        day,
        now.getHours(),
        now.getMinutes(),
        now.getSeconds()
      );
      logShiftDate = targetDate.toISOString();
    }

    await api.post(`/experiments/${experimentId}/logs`, {
      content: newLogContent.value.trim(),
      participants: selectedLogOperators.value.join(', '),
      attachments: uploadedFileNames.value,
      shift_date: logShiftDate
    });
    toast.success("Log card appended into timeline!");
    closeAddLogModal();
    await fetchAllLogs();
  } catch (error) {
    toast.error("Submission blocked.");
  }
};

const enterLogEditMode = () => {
  editLogContent.value = selectedLog.value.content;
  editLogOperators.value = selectedLog.value.participants ? selectedLog.value.participants.split(', ') : [];
  editLogAttachments.value = selectedLog.value.attachments ? [...selectedLog.value.attachments] : [];
  isLogEditingFlow.value = true;
};

const handleEditFileSelection = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (editLogAttachments.value.includes(file.name)) continue;
    
    // Check file size: 50MB limit
    const MAX_SIZE = 50 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      toast.error(`File [${truncateFileName(file.name)}] exceeds the 50MB size limit.`);
      continue;
    }
    
    toast.info(`📤 Appending file: [${truncateFileName(file.name)}]...`);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await api.post('/experiments/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      editLogAttachments.value.push(response.data.filename);
      toast.success(`✅ Added [${truncateFileName(file.name)}] to file stack.`);
    } catch (error) {
      toast.error(`Failed to sync file [${truncateFileName(file.name)}]`);
    }
  }
  event.target.value = '';
};

const removeFileFromEdit = (filename) => {
  editLogAttachments.value = editLogAttachments.value.filter(name => name !== filename);
  toast.success("Removed attachment stack reference.");
};

const handleSaveLogEdit = async () => {
  try {
    await api.put(`/experiments/logs/${selectedLog.value.id}`, {
      content: editLogContent.value.trim(),
      participants: editLogOperators.value.join(', ') || null,
      attachments: editLogAttachments.value
    });
    toast.success("Log record updated flawlessly!");
    isLogEditingFlow.value = false;
    showLogDetailModal.value = false;
    await fetchAllLogs();
  } catch (error) {
    toast.error("Edit tracking rejected.");
  }
};

const openManagePersonnelModal = async () => {
  try {
    const response = await api.get(`/experiments/groups/${activeGroupId.value}/members`);
    allTeamMembers.value = response.data;
    checkedPersonnelIds.value = experiment.value.members.map(m => m.id);
    showPersonnelModal.value = true;
  } catch (error) {
    toast.error("Roster unavailable.");
  }
};

const handleSavePersonnel = async () => {
  try {
    await api.put(`/experiments/${experimentId}/members`, checkedPersonnelIds.value);
    toast.success("Personnel linked to workspace.");
    showPersonnelModal.value = false;
    await fetchExperimentMeta();
  } catch (error) {
    toast.error("Link rejected.");
  }
};

const handleDownloadFile = (filename) => {
  if (!filename) return;
  toast.info(`💾 Retrieving [${truncateFileName(filename, 16)}] bits from central repository...`);
  
  api.get(`/experiments/attachments/${filename}`, { responseType: 'blob' })
    .then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`🎉 File [${truncateFileName(filename, 16)}] successfully streamed!`);
    })
    .catch(() => {
      toast.error("Authorization check failed or file is corrupted on node storage.");
    });
};

const isPreviewOpen = ref(false);
const previewFilename = ref('');
const pdfStreamUrl = ref('');

const triggerPdfPreview = (filename) => {
  if (!filename) return;
  previewFilename.value = filename;
  toast.info(`🔍 Streaming [${truncateFileName(filename, 16)}] into local preview frame...`);
  
  api.get(`/experiments/attachments/${filename}?preview=true`, { responseType: 'blob' })
    .then(response => {
      if (pdfStreamUrl.value) {
        window.URL.revokeObjectURL(pdfStreamUrl.value);
      }
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      pdfStreamUrl.value = url;
      isPreviewOpen.value = true;
      toast.success("Document loaded successfully!");
    })
    .catch(() => {
      toast.error("Access denied or failed to stream document.");
    });
};

const closePdfPreview = () => {
  isPreviewOpen.value = false;
  previewFilename.value = '';
  if (pdfStreamUrl.value) {
    window.URL.revokeObjectURL(pdfStreamUrl.value);
    pdfStreamUrl.value = '';
  }
};

onUnmounted(() => {
  if (pdfStreamUrl.value) {
    window.URL.revokeObjectURL(pdfStreamUrl.value);
  }
});

const getAvatarUrl = (node) => `${api.defaults.baseURL}/experiments/attachments/${node}`;

const allFlattenedAttachments = computed(() => {
  const result = [];
  rawLogs.value.forEach(log => {
    if (log.attachments && log.attachments.length > 0) {
      log.attachments.forEach(file => {
        result.push({ file, log });
      });
    }
  });
  return result;
});

const allFlattenedImages = computed(() => {
  const imageRegex = /\.(png|jpe?g|gif|webp)$/i;
  return allFlattenedAttachments.value.filter(item => imageRegex.test(item.file));
});

const displayedAttachments = computed(() => {
  if (isAttachmentsExpanded.value) {
    return allFlattenedAttachments.value;
  }
  return allFlattenedAttachments.value.slice(0, ATTACHMENTS_LIMIT);
});

const displayedImages = computed(() => {
  if (isGalleryExpanded.value) {
    return allFlattenedImages.value;
  }
  return allFlattenedImages.value.slice(0, GALLERY_LIMIT);
});

const toggleDateExpansion = (date) => {
  if (expandedDates.value.has(date)) {
    expandedDates.value.delete(date);
  } else {
    expandedDates.value.add(date);
  }
};

const isDateExpanded = (date) => {
  return expandedDates.value.has(date);
};

const getDisplayedLogs = (col) => {
  if (isDateExpanded(col.date)) {
    return col.logs;
  }
  return col.logs.slice(0, KANBAN_LOG_LIMIT);
};

const canEditCurrentTask = computed(() => {
  if (!experiment.value) return false;
  if (userRole.value === 'sys_admin' || userRole.value === 'team_admin') return true;
  return experiment.value.members.some(
    m => `${m.first_name} ${m.last_name}`.toLowerCase() === userName.value.toLowerCase()
  );
});

const contributorStats = computed(() => {
  if (!experiment.value || !experiment.value.members) return [];
  const list = experiment.value.members.map(user => {
    let operatorCount = 0;
    let attachmentCount = 0;
    const fullName = `${user.first_name} ${user.last_name}`.toLowerCase().trim();
    
    rawLogs.value.forEach(log => {
      // 1. Calculate operator count (appearances in log.participants)
      if (log.participants) {
        const ops = log.participants.split(',').map(name => name.trim().toLowerCase());
        if (ops.includes(fullName)) {
          operatorCount++;
        }
      }
      
      // 2. Calculate attachments uploaded by this user (logs created by this user)
      if (log.author_id === user.id || (log.author && log.author.id === user.id)) {
        if (log.attachments) {
          attachmentCount += log.attachments.length;
        }
      }
    });
    
    const total = operatorCount + attachmentCount;
    return {
      user,
      logCount: operatorCount, // Map operatorCount to logCount for template compatibility
      attachmentCount,
      total
    };
  });
  const filtered = list.filter(item => item.total > 0);
  filtered.sort((a, b) => b.total - a.total);
  return filtered;
});

const enterTaskEditMode = () => {
  editCurrentTaskInput.value = experiment.value.current_task || '';
  isEditingCurrentTask.value = true;
};

const cancelTaskEdit = () => {
  isEditingCurrentTask.value = false;
  editCurrentTaskInput.value = '';
};

const handleSaveCurrentTask = async () => {
  try {
    const res = await api.put(`/experiments/${experiment.value.id}`, {
      current_task: editCurrentTaskInput.value.trim()
    });
    experiment.value.current_task = res.data.current_task;
    isEditingCurrentTask.value = false;
    toast.success("Currently executing task successfully updated!");
  } catch (error) {
    toast.error(error.response?.data?.detail || "Failed to update task.");
  }
};

const triggerImageLightbox = (filename, uploader, logContext) => {
  const token = localStorage.getItem('token') || '';
  lightboxFilename.value = filename;
  lightboxUploader.value = uploader;
  lightboxContext.value = logContext;
  lightboxImageUrl.value = `${api.defaults.baseURL}/experiments/attachments/${filename}?preview=true&token=${token}`;
  isLightboxOpen.value = true;
};

const closeImageLightbox = () => {
  isLightboxOpen.value = false;
  lightboxImageUrl.value = '';
  lightboxFilename.value = '';
  lightboxUploader.value = '';
  lightboxContext.value = '';
};

const handleAttachmentClick = (filename, uploader = 'Unknown', logContext = '') => {
  if (!filename) return;
  const lowercaseName = filename.toLowerCase();
  
  if (lowercaseName.endsWith('.pdf')) {
    const token = localStorage.getItem('token') || '';
    const url = `${api.defaults.baseURL}/experiments/attachments/${filename}?preview=true&token=${token}`;
    window.open(url, '_blank');
    toast.info(`📖 Opening PDF preview [${truncateFileName(filename, 16)}] in new tab...`);
  } else if (/\.(png|jpe?g|gif|webp)$/i.test(lowercaseName)) {
    triggerImageLightbox(filename, uploader, logContext);
  } else {
    handleDownloadFile(filename);
  }
};

const getImageStreamUrl = (filename) => {
  const token = localStorage.getItem('token') || '';
  return `${api.defaults.baseURL}/experiments/attachments/${filename}?preview=true&token=${token}`;
};

const closeLogModal = () => { showLogDetailModal.value = false; selectedLog.value = null; isLogEditingFlow.value = false; };
const openLogDetails = (log) => { selectedLog.value = log; isLogEditingFlow.value = false; showLogDetailModal.value = true; };
const closeModal = () => { showLogDetailModal.value = false; selectedLog.value = null; };
const formatDateToYYYYMMDD = (date) => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const openAddLogModal = (targetDate = null) => {
  addLogSelectedDate.value = targetDate;
  if (targetDate) {
    addLogDateInput.value = formatDateToYYYYMMDD(parseUTC(targetDate));
  } else {
    addLogDateInput.value = formatDateToYYYYMMDD(new Date());
  }
  selectedLogOperators.value = [userName.value];
  showAddLogModal.value = true;
};
const closeAddLogModal = () => {
  showAddLogModal.value = false;
  newLogContent.value = '';
  uploadedFileNames.value = [];
  selectedLogOperators.value = [];
  addLogSelectedDate.value = null;
  addLogDateInput.value = '';
};
const closePersonnelModal = () => { showPersonnelModal.value = false; };
const goBackHome = (groupId) => {
  if (typeof groupId === 'number') {
    localStorage.setItem('activeGroupId', groupId);
  }
  router.push('/');
};
const handleLogout = () => { localStorage.clear(); router.push('/login'); };
const handleDeleteExperiment = async () => {
  const isConfirmed = await confirm(
    "Are you sure you want to permanently delete this experiment project? This will erase all logs, checklists, bulletins, and events linked to it. This action CANNOT be undone.",
    "⚠️ Delete Experiment Project"
  );
  if (!isConfirmed) return;

  try {
    await api.delete(`/experiments/${experimentId}`);
    toast.success("Experiment project deleted successfully.");
    router.push('/');
  } catch (error) {
    toast.error(error.response?.data?.detail || "Failed to delete experiment project.");
  }
};
const parseUTC = (isoStr) => {
  if (!isoStr || typeof isoStr !== 'string') return null;
  let formatted = isoStr;
  if (!isoStr.endsWith('Z') && !isoStr.includes('+') && !/-\d{2}:\d{2}$/.test(isoStr)) {
    formatted = isoStr + 'Z';
  }
  return new Date(formatted);
};

const formatTimeOnly = (iso) => {
  const d = parseUTC(iso);
  if (!d) return '';
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${mm}-${dd} ${hh}:${min}`;
};
const groupedColumns = computed(() => {
  if (rawLogs.value.length === 0) return [];
  const map = {};
  rawLogs.value.forEach(log => {
    const dateStr = parseUTC(log.shift_date).toLocaleDateString();
    if (!map[dateStr]) map[dateStr] = [];
    map[dateStr].push(log);
  });
  
  const columns = Object.keys(map).map(date => {
    const representativeDate = parseUTC(map[date][0].shift_date);
    const dateMidnight = new Date(
      representativeDate.getFullYear(),
      representativeDate.getMonth(),
      representativeDate.getDate()
    );
    return { date, logs: map[date], timeVal: dateMidnight.getTime() };
  });
  
  columns.sort((a, b) => b.timeVal - a.timeVal);
  return columns;
});
</script>

<style>
/* 全局弹窗控制样式 (Ensure Teleport views keep full visual fidelity) */
.modal-backdrop {
  position: fixed !important; top: 0 !important; left: 0 !important;
  width: 100vw !important; height: 100vh !important;
  background: rgba(15, 23, 42, 0.6) !important;
  backdrop-filter: blur(8px) !important; -webkit-backdrop-filter: blur(8px) !important;
  display: flex !important; justify-content: center !important; align-items: center !important;
  z-index: var(--z-overlay) !important;
}

.log-detail-modal {
  background: #ffffff !important; width: 95% !important; max-width: 580px !important;
  border-radius: 12px !important; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
  padding: 30px !important; box-sizing: border-box !important;
  animation: modal-pop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-pop {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 16px; }
.modal-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: #0f172a; }
.modal-header-meta { display: flex; align-items: center; gap: 14px; text-align: left; }
.modal-avatar-logo { font-size: 26px; }
.modal-subtitle { margin: 2px 0 0 0; font-size: 12px; color: var(--text-muted); text-align: left; }

.modal-log-content { background: #f8fafc; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 18px; margin: 16px 0; text-align: left; max-height: 280px; overflow-y: auto; }
.full-log-paragraph { font-size: 14px; color: #1e293b; line-height: 1.6; margin: 0; white-space: pre-wrap; }

.modal-log-footer { display: flex; flex-direction: column; gap: 8px; text-align: left; border-top: 1px solid var(--border-color); padding-top: 14px; }
.footer-meta-item { font-size: 13px; display: flex; align-items: center; gap: 8px; color: #334155; }
.footer-badge { background: #e2e8f0; font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; color: #475569; }
.footer-attach-link { font-size: 12px; font-weight: 600; color: var(--primary-color); }
.modal-edit-action-row { display: flex; justify-content: flex-end; margin-top: 14px; }

.btn-inline-add {
  padding: 6px 14px !important; background: #f1f5f9 !important; color: #1e293b !important;
  border: 1px solid #cbd5e1 !important; border-radius: 6px !important; font-size: 13px !important;
  font-weight: 600 !important; cursor: pointer !important; display: inline-block !important;
}
.btn-inline-add:hover { background: #e2e8f0 !important; color: #0f172a !important; }

.modal-form-flow { text-align: left; margin-top: 10px; display: flex; flex-direction: column; gap: 14px; }
.modal-form-group { display: flex; flex-direction: column; }
.modal-form-group label { font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--text-main); }
.modal-form-group input, .modal-form-group textarea { padding: 8px 12px; font-size: 14px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); outline: none; background: #fafbfc; box-sizing: border-box; width: 100%; }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 16px; }
.btn-cancel { padding: 6px 14px; background: transparent; border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; color: var(--text-muted); font-size: 13px; }
.btn-submit { padding: 6px 14px; background: var(--primary-color); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer; font-weight: 600; font-size: 13px; }
.btn-submit:disabled { background: #cbd5e1; color: #94a3b8; cursor: not-allowed; }
.btn-close-x { background: transparent; border: none; font-size: 24px; color: #94a3b8; cursor: pointer; padding: 0; line-height: 1; }

.team-checkbox-matrix { border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; background: #fafbfc; max-height: 130px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; box-sizing: border-box; }
.large-pool { max-height: 220px !important; }
.matrix-item { display: flex; align-items: center; gap: 8px; text-align: left; }
.matrix-item input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; margin: 0; }
.matrix-item label { font-size: 13px; cursor: pointer; margin: 0; font-weight: normal; color: #334155; }
.file-uploader-box { display: flex; align-items: center; gap: 10px; margin-top: 4px; }
.btn-remove-file { background: #fee2e2; color: #ef4444; border: 1px solid #fca5a5; padding: 2px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; }

.modal-attachment-list { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
.modal-file-row { text-align: left; }
.form-files-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.form-file-chip {
  display: flex; align-items: center; gap: 8px; background: #eff6ff; border: 1px solid #bfdbfe;
  padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; color: #1d4ed8;
}
.btn-delete-chip {
  background: transparent; border: none; color: #3b82f6; font-size: 14px; font-weight: bold;
  cursor: pointer; padding: 0; line-height: 1;
}
.btn-delete-chip:hover { color: #1d4ed8; }

.format-select-full {
  padding: 8px 12px !important; font-size: 14px !important; border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-sm) !important; outline: none !important; background: #fafbfc !important; width: 100% !important; box-sizing: border-box !important;
}
</style>

<style scoped>
.detail-layout { height: 100%; overflow: hidden; background-color: var(--bg-primary); }
.detail-main {
  margin-top: 64px;
  margin-left: 240px;
  padding: 24px 32px;
  box-sizing: border-box;
  height: calc(100vh - 64px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

@media (max-width: 1023px) {
  .detail-main {
    height: calc(100vh - 64px) !important;
    overflow-y: auto !important;
  }
  .workspace-split {
    flex-direction: column !important;
    height: auto !important;
    overflow-y: visible !important;
    gap: 24px !important;
  }
  .canvas-center {
    height: auto !important;
    overflow-y: visible !important;
    padding-right: 0 !important;
  }
  .utility-dock {
    width: 100% !important;
    height: auto !important;
    overflow-y: visible !important;
    padding-right: 0 !important;
  }
  .kanban-scroll-row {
    padding: 0 16px 16px 16px !important;
  }
}

@media (max-width: 767px) {
  .detail-main {
    margin-left: 0 !important;
    padding: 16px !important;
  }
  .exp-meta-bar {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 16px !important;
  }
  .log-detail-modal {
    padding: 20px !important;
  }
}

.exp-meta-bar { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1px solid var(--border-color); padding-bottom: 16px; margin-bottom: 24px; flex-shrink: 0; }
.btn-back { background: transparent; border: none; color: var(--primary-color); font-size: 13px; font-weight: 600; cursor: pointer; padding: 0; }
.title-row { display: flex; align-items: center; gap: 16px; margin: 4px 0 6px 0; }
.title-row h2 { margin: 0; font-size: 22px; font-weight: 700; color: var(--text-main); letter-spacing: -0.5px; }

/* 状态指示牌视觉属性 */
.status-indicator { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.status-indicator.running { background: #ecfdf5; color: var(--success-color); }
.status-indicator.paused { background: #fffbeb; color: #d97706; }
.status-indicator.stopped { background: #fef2f2; color: #ef4444; }
.status-indicator.archived { background: #f1f5f9; color: #64748b; }

.meta-tags { display: flex; gap: 6px; }
.hash-tag { font-size: 12px; background: #e2e8f0; color: #475569; padding: 2px 8px; border-radius: 4px; }

.btn-edit-meta { padding: 6px 12px; background: #fff; border: 1px solid var(--border-color); border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; font-weight: 600; color: var(--text-main); }
.btn-edit-meta:hover { background: #f8fafc; border-color: #cbd5e1; }

.btn-delete-meta { padding: 6px 12px; background: #fff; border: 1px solid #fecaca; border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; font-weight: 600; color: #ef4444; margin-left: 8px; transition: all 0.15s ease; }
.btn-delete-meta:hover { background: #fef2f2; border-color: #fca5a5; }

.form-input-date {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  box-sizing: border-box;
  background-color: #fff;
  color: var(--text-main);
}
.form-input-date:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.btn-record-log {
  background: var(--primary-color);
  color: #fff;
  border: none;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(37,99,235,0.1);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-record-log:hover {
  background: var(--primary-hover);
}

.workspace-split {
  display: flex;
  gap: 28px;
  align-items: stretch;
  flex: 1;
  min-height: 0;
}
.canvas-center {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  overflow-y: auto;
  padding-right: 8px;
}
.canvas-center::-webkit-scrollbar {
  width: 6px;
}
.canvas-center::-webkit-scrollbar-track {
  background: transparent;
}
.canvas-center::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.canvas-center::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
.utility-dock {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
}
.utility-dock::-webkit-scrollbar {
  width: 6px;
}
.utility-dock::-webkit-scrollbar-track {
  background: transparent;
}
.utility-dock::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.utility-dock::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.content-block { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 24px; box-shadow: var(--shadow-sm); flex-shrink: 0; }
.no-padding { padding: 0 !important; }
.bg-kanban-track { background: #f8fafc; }
.padding-inside { padding: 20px 24px 10px 24px; }

.block-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.block-title { margin: 0; font-size: 14px; font-weight: 600; color: var(--text-main); }
.editor-controls { display: flex; align-items: center; gap: 10px; }
.format-select { padding: 4px 8px; border: 1px solid var(--border-color); border-radius: 4px; font-size: 12px; font-weight: 600; background: #fff; outline: none; }
.btn-toggle-mode { background: #fff; border: 1px solid var(--border-color); padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 600; }

.markdown-view-wrapper { text-align: left; background: #fff; padding: 20px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); }
.plain-text-body { white-space: pre-wrap; font-family: monospace; font-size: 13.5px; line-height: 1.6; margin: 0; color: #334155; text-align: left; background: #fafbfc; padding: 12px; border-radius: 4px; border: 1px solid var(--border-color); }

.static-textarea { width: 100%; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 12px; font-family: monospace; font-size: 13px; background: #fafbfc; box-sizing: border-box; resize: vertical; outline: none; }
.editor-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px; }
.btn-cancel-inline { padding: 4px 12px; background: #fff; border: 1px solid var(--border-color); border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-save-inline { padding: 4px 12px; background: var(--primary-color); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; font-weight: 600; }

.btn-add-participant { background: #eff6ff; color: var(--primary-color); border: 1px solid #bfdbfe; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 600; }
.participants-list-row { display: flex; gap: 12px; flex-wrap: wrap; text-align: left; }
.participant-chip { display: flex; align-items: center; gap: 10px; background: #f1f5f9; padding: 6px 12px; border-radius: 6px; border: 1px solid #e2e8f0; }
.p-avatar { font-size: 14px; }
.p-avatar-img { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; }
.log-author-avatar-img { width: 14px; height: 14px; border-radius: 50%; object-fit: cover; vertical-align: middle; margin-right: 4px; display: inline-block; }
.p-info { display: flex; flex-direction: column; }
.p-name { font-size: 13px; font-weight: 600; color: var(--text-main); }
.p-role { font-size: 10px; color: var(--text-muted); font-weight: bold; }
.empty-personnel-tip { font-size: 13px; color: var(--text-muted); text-align: left; background: #fffdf5; padding: 12px; border: 1px dashed #d97706; border-radius: var(--radius-sm); }

.kanban-tip { font-size: 11px; color: var(--text-muted); }
.kanban-scroll-row { display: flex; gap: 16px; overflow-x: auto; padding: 0 24px 20px 24px; align-items: flex-start; }
.kanban-column { width: 290px; flex-shrink: 0; background: #f1f5f9; border-radius: var(--radius-md); padding: 12px; box-sizing: border-box; }
.col-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.col-header h4 { margin: 0; font-size: 13px; font-weight: 600; color: #475569; }
.btn-add-log-inline { background: transparent; border: none; font-size: 16px; color: var(--text-muted); cursor: pointer; font-weight: bold; }
.cards-stack { display: flex; flex-direction: column; gap: 10px; }

.log-card { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 12px; box-shadow: var(--shadow-sm); }
.log-card-meta { display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }
.logger-name { color: var(--text-main); }
.log-text { font-size: 13px; color: #334155; line-height: 1.4; margin: 0 0 8px 0; word-break: break-all; text-align: left; }

.card-action-row { margin-bottom: 10px; text-align: left; }
.btn-read-more { background: transparent; border: none; color: var(--primary-color); font-size: 12px; font-weight: 600; cursor: pointer; padding: 0; }
.log-participants { font-size: 11px; color: var(--text-muted); background: #f8fafc; padding: 4px 6px; border-radius: 4px; border: 1px solid #f1f5f9; text-align: left; margin-bottom: 6px; }
.log-card-attach { font-size: 11px; font-weight: 600; color: var(--primary-color); text-align: left; }

.empty-kanban-state { text-align: center; padding: 40px; color: var(--text-muted); }
.empty-kanban-state p { font-size: 14px; margin-bottom: 12px; font-weight: 500; }
.btn-add-first-log { background: var(--primary-color); color: white; border: none; padding: 6px 14px; font-size: 13px; font-weight: 600; border-radius: var(--radius-sm); cursor: pointer; }

.dock-panel { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 20px; flex-shrink: 0; }
.panel-title-row h3 { margin: 0; font-size: 14px; font-weight: 600; text-align: left; margin-bottom: 12px; }
.task-list { display: flex; flex-direction: column; gap: 10px; }
.task-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f8fafc; border: 1px solid var(--border-color); border-radius: var(--radius-sm); }
.task-main { display: flex; flex-direction: column; text-align: left; }
.task-name { font-size: 13px; font-weight: 500; }
.task-deadline, .file-info { font-size: 11px; color: var(--text-muted); }
.task-status.verified { background: #d1fae5; color: #065f46; font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }

.footer-attach-link-active { color: var(--primary-color) !important; font-weight: 600; text-decoration: underline !important; cursor: pointer !important; }
.card-attach-clickable { color: var(--primary-color); font-weight: 600; text-decoration: none; font-size: 11px; }
.card-attach-clickable:hover { text-decoration: underline; }

.log-card-attachments { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.card-attach-chip {
  background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px;
  padding: 2px 6px; display: inline-flex; align-items: center; max-width: 100%; box-sizing: border-box;
}
.card-attach-chip:hover { background: #e2e8f0; }

/* 🆕 1. 第一栏折叠式抽屉大纲专属过渡动画 (丝滑 Slide-Fade 引擎) */
.slide-fade-enter-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-12px);
  opacity: 0;
}

.header-left-meta { display: flex; align-items: center; gap: 16px; }
.collapse-hint-text {
  font-size: 12.5px; color: var(--primary-color); font-weight: 600;
  cursor: pointer; user-select: none;
}
.collapse-hint-text:hover { text-decoration: underline; }
.btn-expand-trigger {
  background: #f1f5f9; border: 1px solid var(--border-color); padding: 4px 10px;
  border-radius: 4px; font-size: 12px; font-weight: 600; color: #475569; cursor: pointer;
}
.btn-expand-trigger:hover { background: #e2e8f0; color: #0f172a; }

/* 🆕 2. 第二栏置顶通告通知板专属高级学术调配色泽 */
.bg-notification-board {
  background: #fffdf5 !important;
  border: 1px solid #fde68a !important;
}
.font-yellow { color: #b45309 !important; }
.bulletin-count-badge {
  background: #fef3c7; color: #b45309; font-size: 11px;
  font-weight: 600; padding: 2px 8px; border-radius: 20px;
}
.bulletins-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.bulletin-item {
  display: flex; align-items: flex-start; gap: 12px; background: #ffffff;
  border: 1px solid #fde68a; border-radius: 6px; padding: 12px;
  position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.bulletin-symbol { font-size: 16px; }
.bulletin-content-wrapper { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.bulletin-text { margin: 0; font-size: 13.5px; color: #78350f; line-height: 1.4; font-weight: 500; }
.bulletin-author { font-size: 11px; color: #b45309; font-weight: 600; }
.btn-delete-bulletin {
  background: transparent; border: none; font-size: 18px; color: #d97706;
  cursor: pointer; line-height: 1; padding: 0;
}
.btn-delete-bulletin:hover { color: #b45309; }
.empty-bulletins {
  font-size: 13.5px; color: #b45309; padding: 16px; text-align: center;
  background: #ffffff; border: 1px dashed #fde68a; border-radius: 6px; margin-bottom: 12px;
}
.bulletin-quick-post { display: flex; gap: 10px; margin-top: 12px; }
.bulletin-quick-post input {
  flex: 1; padding: 8px 12px; border: 1px solid #fde68a; border-radius: 6px;
  font-size: 13px; outline: none; background: #ffffff; box-sizing: border-box;
}
.bulletin-quick-post input:focus {
  border-color: #d97706; box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.12);
}
.btn-post-bulletin {
  background: #d97706; color: white; border: none; padding: 8px 16px;
  border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-post-bulletin:hover { background: #b45309; }

/* PDF Preview Modal Styles */
.pdf-preview-backdrop {
  z-index: 200 !important;
  background: rgba(15, 23, 42, 0.65) !important;
  backdrop-filter: blur(8px) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.pdf-preview-box {
  width: 90% !important;
  max-width: 1080px !important;
  height: 85vh !important;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalScaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.pdf-preview-header {
  padding: 16px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.pdf-preview-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.pdf-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-download-pdf-preview {
  background: #2563eb;
  color: #ffffff;
  border: none;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-download-pdf-preview:hover {
  background: #1d4ed8;
}

.btn-close-pdf-preview {
  background: none;
  border: none;
  font-size: 24px;
  color: #64748b;
  cursor: pointer;
  transition: color 0.2s;
  padding: 0 4px;
  line-height: 1;
}

.btn-close-pdf-preview:hover {
  color: #ef4444;
}

.pdf-preview-body {
  flex: 1;
  min-height: 0;
  background: #475569;
  position: relative;
}

.pdf-iframe-element {
  width: 100%;
  height: 100%;
  border: none;
  background: #ffffff;
}

/* Custom layout eye buttons */
.btn-preview-attachment {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #475569;
  font-size: 10px;
  padding: 1px 3px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 6px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn-preview-attachment:hover {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

.btn-preview-attachment-modal {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #2563eb;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
  margin-left: 8px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
}
.btn-preview-attachment-modal:hover {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

.btn-preview-attachment-tiny {
  background: none;
  border: none;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn-preview-attachment-tiny:hover {
  background: #e2e8f0;
}

/* Image Gallery Panel Styles */
.image-gallery-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
  flex-shrink: 0;
}

.gallery-count-badge {
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 12px;
  margin-left: 6px;
}

.image-gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.gallery-item-card {
  aspect-ratio: 1 / 1;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  cursor: pointer;
  background: #f8fafc;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.gallery-item-card:hover {
  transform: scale(1.06);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #bfdbfe;
}

.gallery-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.btn-toggle-expand {
  display: block;
  width: 100%;
  text-align: center;
  background: none;
  border: 1px dashed var(--border-color, #e2e8f0);
  color: #64748b;
  font-size: 11.5px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 12px;
  transition: all 0.2s;
}

.btn-toggle-expand:hover {
  background: #f8fafc;
  color: #2563eb;
  border-color: #bfdbfe;
}

/* 📊 Premium Leaderboard CSS Tooltip controls */
.info-tooltip-container:hover .info-tooltip-content {
  visibility: visible !important;
  opacity: 1 !important;
}
</style>