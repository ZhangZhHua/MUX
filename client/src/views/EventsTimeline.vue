<template>
  <div class="dashboard-layout">
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" />
    
    <Sidebar :groups="groups" :currentGroupId="currentGroupId" @group-change="handleGroupChange" />

    <main class="main-content">
      <div class="workspace-container">
        
        <!-- Left Main Area: Weekly Timeline -->
        <div class="workspace-left">
          <div class="timeline-header-bar">
            <div class="header-title-zone">
              <span class="view-pill">📅 Weekly Schedule</span>
              <h2>{{ formatWeekRangeText }}</h2>
            </div>
            
            <!-- <div class="header-actions">
              <button 
                class="btn-create-event" 
                v-if="userRole !== 'member'"
                @click="openCreateModal"
              >
                + Add Event
              </button>
            </div> -->
          </div>

          <!-- Weekly Schedule Days (Date 1 to Date 7) -->
          <div class="weekly-timeline-flow">
            <div 
              v-for="day in weeklyDays" 
              :key="day.dateStr" 
              :id="'day-section-' + day.dateStr"
              class="timeline-day-section"
              :class="{ 'is-today': day.isToday }"
            >
              <div class="day-indicator">
                <div class="day-indicator-left">
                  <span class="day-name">{{ day.dayName }}</span>
                  <span class="day-date">{{ day.displayDate }}</span>
                  <span v-if="day.isToday" class="today-badge">TODAY</span>
                </div>
                <button 
                  class="btn-day-add-event" 
                  v-if="userRole !== 'member'"
                  @click="openCreateModal(day.dateStr)"
                >
                  + Add Event
                </button>
              </div>

              <div class="day-events-list">
                
                <div 
                  v-for="event in day.events" 
                  :key="event.unique_key" 
                  class="event-card"
                  :class="{ 'is-important-card': event.is_important }"
                >
                  <div class="event-card-header">
                    <div class="event-meta-row">
                      <!-- Event tags -->
                      <div class="event-tags-row" v-if="event.tags && event.tags.length > 0">
                        <span 
                          v-for="tag in event.tags" 
                          :key="tag.id" 
                          class="event-tag-badge"
                          :class="getTagColorClass(tag.name)"
                        >
                          {{ tag.name }}
                        </span>
                      </div>
                      <span v-if="event.is_important" class="important-chip">🔥 Milestone</span>
                    </div>

                    <div class="event-time-range-row">
                      <span class="time-range-label">🕒 {{ formatEventTimeRange(event.start_date, event.end_date) }}</span>
                    </div>

                    <div class="event-title-row">
                      <h3 class="event-title">{{ event.title }}</h3>
                      
                      <!-- CRUD Actions -->
                      <div class="event-card-actions" v-if="canManageEvent(event)">
                        <button class="card-edit-button" @click="openEditModal(event)">EDIT</button>
                      </div>
                    </div>

                    <div class="event-author-row">
                      <!-- Experiment association link -->
                      <span v-if="event.experiment_id" class="exp-link-badge" @click="navigateToExperiment(event.experiment_id)">
                        🔬 Linked Exp: {{ event.experiment_title || `#${event.experiment_id}` }}
                      </span>

                      <!-- Recurrence indicator -->
                      <span v-if="event.recurrence_rule" class="recurrence-badge" :title="getRecurrenceTooltip(event)">
                        🔁 Recurrence: {{ formatRecurrenceText(event.recurrence_rule) }}
                      </span>
                    </div>

                    <!-- Event participants list (显示参与人员列表，无头像) -->
                    <div class="event-participants-row" v-if="event.participants && event.participants.length > 0">
                      <span class="participants-label">Participants:</span>
                      <span 
                        v-for="p in event.participants" 
                        :key="p.id" 
                        class="participant-badge"
                      >
                        {{ p.first_name }} {{ p.last_name }}
                      </span>
                    </div>
                  </div>

                  <!-- Event Introduction (事件介绍) -->
                  <div class="event-body">
                    <p class="event-description">{{ event.description }}</p>

                    <!-- Attachments -->
                    <div v-if="event.attachments && event.attachments.length > 0" class="event-attachments-section">
                      <div class="attachments-title">📎 Attachments:</div>
                      <div class="attachments-grid">
                        <div 
                          v-for="file in event.attachments" 
                          :key="file.name" 
                          class="attachment-chip"
                          :title="file.name"
                        >
                          <span class="attach-icon">📄</span>
                          <span 
                            class="attach-name-link"
                            @click="handleAttachmentClick(file.name, event.author ? `${event.author.first_name} ${event.author.last_name}` : 'Unknown')"
                          >
                            {{ truncateFileName(file.name, 22) }}
                          </span>
                          <span class="attach-source-badge" :class="file.is_referenced ? 'ref-source' : 'upload-source'">
                            {{ file.is_referenced ? 'exp' : 'local' }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Card Footer: Collapse/Expand control and Comment summary -->
                  <div class="event-card-footer">
                    <button class="btn-toggle-comments" @click="toggleComments(event)">
                      💬 Comments ({{ event.commentsCount || 0 }}) 
                      <span class="arrow-indicator">{{ expandedComments[event.unique_key] ? '▲' : '▼' }}</span>
                    </button>
                  </div>

                  <!-- Comments Drawer Section -->
                  <div v-if="expandedComments[event.unique_key]" class="event-comments-drawer">
                    <div class="comments-list-wrapper">
                      <div v-if="loadingComments[event.unique_key]" class="comments-loading">
                        Syncing conversations...
                      </div>
                      <div v-else-if="!commentsData[event.id] || commentsData[event.id].length === 0" class="empty-comments">
                        No conversations logged. Write the first comment below.
                      </div>
                      <div v-else class="comments-list">
                        <div v-for="c in commentsData[event.id]" :key="c.id" class="comment-item">
                          <div class="comment-meta">
                            <span class="comment-author">{{ c.author?.first_name }} {{ c.author?.last_name }}</span>
                            <span class="comment-time">{{ formatTime(c.created_at) }}</span>
                          </div>
                          <p class="comment-text">{{ c.content }}</p>
                        </div>
                      </div>
                    </div>

                    <!-- Post comment input -->
                    <form @submit.prevent="submitComment(event)" class="post-comment-form">
                      <input 
                        type="text" 
                        v-model="commentInputs[event.unique_key]" 
                        placeholder="Write a lab log comment..." 
                        required
                        class="comment-input-field"
                      />
                      <button type="submit" class="btn-post-comment" :disabled="!commentInputs[event.unique_key]?.trim()">
                        Send
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Sidebar Area -->
        <div class="workspace-right">
          <!-- Calendar Selector Widget (日历插件 / 可选时间) -->
          <div class="intelligence-card alert-board-panel calendar-widget-card">
            <div class="intel-header">
              <h3>📅 Choose View Date</h3>
            </div>
            <div class="calendar-widget-body">
              <!-- Calendar Month Title and Navigation -->
              <div class="calendar-month-header">
                <button type="button" class="btn-month-nav" @click="shiftCalendarMonth(-1)" title="Previous Month">◀️</button>
                <div class="month-center-group">
                  <div class="calendar-month-year-selects">
                    <select 
                      :value="calendarMonth.getMonth()" 
                      @change="onMonthSelectChange"
                      class="calendar-select select-month"
                    >
                      <option v-for="(m, idx) in monthNames" :key="idx" :value="idx">{{ m }}</option>
                    </select>
                    <select 
                      :value="calendarMonth.getFullYear()" 
                      @change="onYearSelectChange"
                      class="calendar-select select-year"
                    >
                      <option v-for="y in yearRange" :key="y" :value="y">{{ y }}</option>
                    </select>
                  </div>
                  <button type="button" class="btn-today" @click="jumpToToday" title="Back to Today">Today</button>
                </div>
                <button type="button" class="btn-month-nav" @click="shiftCalendarMonth(1)" title="Next Month">▶️</button>
              </div>

              <!-- Days Grid Header -->
              <div class="calendar-days-grid-header">
                <span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span><span>Su</span>
              </div>

              <!-- Days Grid -->
              <div class="calendar-days-grid">
                <div 
                  v-for="cell in calendarGridDays" 
                  :key="cell.dateStr"
                  class="calendar-day-cell"
                  :class="{ 
                    'other-month': !cell.isCurrentMonth,
                    'in-active-week': isCellInActiveWeek(cell.dateStr),
                    'selected-day': isCellSelected(cell.dateStr),
                    'today-day': isCellToday(cell.dateStr)
                  }"
                  @click="selectCalendarDate(cell.date)"
                >
                  <span class="day-number-text">{{ cell.dayNum }}</span>
                  <span 
                    v-if="datesWithEvents[cell.dateStr]" 
                    class="calendar-day-dot"
                  ></span>
                </div>
              </div>
            </div>
          </div>

          <!-- Important Events Overview (重要事件总览) -->
          <div class="intelligence-card alert-board-panel important-events-card">
            <div class="intel-header">
              <h3>🔥 Milestone Overview</h3>
              <span class="pulse-red-dot"></span>
            </div>
            
            <div class="important-events-body">
              <div v-if="importantEvents.length === 0" class="empty-important-state">
                No milestones scheduled for this week range.
              </div>
              <div v-else class="important-timeline">
                <div 
                  v-for="item in importantEvents" 
                  :key="item.unique_key" 
                  class="important-timeline-item"
                  @click="scrollToEvent(item.unique_key)"
                >
                  <div class="item-indicator-dot"></div>
                  <div class="item-content-box">
                    <span class="item-date-badge">{{ item.instance_date }}</span>
                    <h4 class="item-title">{{ item.title }}</h4>
                    <div class="item-tags">
                      <span v-for="t in item.tags" :key="t.id" class="mini-tag">{{ t.name }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Create / Edit Event Modal -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showEventModal" @click.self="closeEventModal">
        <div class="modal-box event-modal">
          <div class="modal-header">
            <h3>{{ isEditMode ? 'Modify Lab Event Node' : 'Spawn Lab Event Node' }}</h3>
            <button class="btn-close-x" @click="closeEventModal">&times;</button>
          </div>
          
          <form @submit.prevent="handleSubmitEvent" class="modal-form-flow event-form-container">
            <div class="modal-form-scroll-wrapper">
              <!-- Event Title -->
            <div class="modal-form-group">
              <label>Event Title / Topic *</label>
              <input type="text" v-model="formEvent.title" required placeholder="e.g. Group Meeting, Spectroscopy Run..." />
            </div>

            <!-- Event Description (事件介绍) -->
            <div class="modal-form-group">
              <label>Event Description / Directive *</label>
              <textarea v-model="formEvent.description" required rows="4" placeholder="Describe the objectives and plans for this event node..."></textarea>
            </div>

            <!-- Date & Time Selection -->
            <div class="modal-form-row">
              <div class="modal-form-group flex-1">
                <label>Scheduled Date *</label>
                <input type="date" v-model="formEvent.dateStr" required />
              </div>
              <div class="modal-form-group flex-1">
                <label>Start Time *</label>
                <input type="time" v-model="formEvent.timeStr" required />
              </div>
              <div class="modal-form-group flex-1">
                <label>End Time *</label>
                <input type="time" v-model="formEvent.endTimeStr" required />
              </div>
            </div>

            <!-- Experiment Link -->
            <div class="modal-form-group">
              <label>Link to Research Experiment (Optional)</label>
              <select v-model="formEvent.experiment_id" @change="handleExperimentChange" class="modal-select-input">
                <option :value="null">-- No Experiment Linked --</option>
                <option v-for="exp in allExperiments" :key="exp.id" :value="exp.id">
                  🔬 [ID: #{{ exp.id }}] {{ exp.title }}
                </option>
              </select>
            </div>

            <!-- Choose Participants -->
            <div class="modal-form-group">
              <label>Select Participants (选择参与人员)</label>
              <div class="participants-checkbox-list">
                <label 
                  v-for="user in allUsers" 
                  :key="user.id" 
                  class="participant-checkbox-item"
                  :class="{ checked: formEvent.participants.includes(user.id) }"
                >
                  <input 
                    type="checkbox" 
                    :value="user.id" 
                    v-model="formEvent.participants" 
                    class="participant-checkbox-input"
                  />
                  <span class="participant-checkbox-name">{{ user.first_name }} {{ user.last_name }}</span>
                </label>
              </div>
            </div>

            <!-- Tag categorization and Creation -->
            <div class="modal-form-group">
              <label>Event Type / Tags (Meeting, Experiment, etc.)</label>
              
              <!-- Select Existing Tags -->
              <div class="tag-selector-chip-container" v-if="allAvailableTags.length > 0">
                <span 
                  v-for="tag in allAvailableTags" 
                  :key="tag.id" 
                  class="tag-selector-pill"
                  :class="{ selected: formEvent.tags.includes(tag.name) }"
                  @click="toggleTagSelection(tag.name)"
                >
                  {{ tag.name }}
                </span>
              </div>
              
              <!-- Add Custom Tag -->
              <div class="custom-tag-adder">
                <input 
                  type="text" 
                  v-model="customTagInput" 
                  placeholder="Create custom tag on-the-fly..." 
                  class="custom-tag-input"
                  @keydown.enter.prevent="addCustomTag"
                />
                <button type="button" @click="addCustomTag" class="btn-add-tag-inline">Add</button>
              </div>
            </div>

            <!-- Recurrence Setup -->
            <div class="modal-form-row">
              <div class="modal-form-group flex-1">
                <label>Recurrence Rule</label>
                <select v-model="formEvent.recurrence_rule">
                  <option :value="null">No Recurrence (Standalone)</option>
                  <option value="weekly">Every Week (Weekly)</option>
                  <option value="biweekly">Every 2 Weeks (Bi-weekly)</option>
                  <option value="monthly">Every Month (Monthly)</option>
                </select>
              </div>
              <div class="modal-form-group flex-1" v-if="formEvent.recurrence_rule">
                <label>Recurrence End Date (Optional)</label>
                <input type="date" v-model="formEvent.recurrence_end_date_str" placeholder="Defaults to indefinitely" />
              </div>
            </div>

            <!-- Attachments Sourcing -->
            <div class="modal-form-group">
              <label>Event Attachments</label>
              
              <!-- Sourced from linked experiment -->
              <div v-if="formEvent.experiment_id && expAttachments.length > 0" class="exp-attachments-selector">
                <span class="sub-label">Reference Attachments from linked Experiment:</span>
                <div class="checkbox-options-grid">
                  <label v-for="file in expAttachments" :key="file" class="checkbox-option-item" :class="{ 'checked-item': selectedExpFiles.includes(file) }">
                    <input 
                      type="checkbox" 
                      :value="file" 
                      v-model="selectedExpFiles"
                      class="ref-attachment-input"
                    />
                    <span class="ref-attachment-text" :title="file">📎 {{ truncateFileName(file, 22) }}</span>
                  </label>
                </div>
              </div>
              <div v-else-if="formEvent.experiment_id" class="info-alert-text">
                💡 No attachments found on the linked experiment logs.
              </div>

              <!-- Upload local file -->
              <div class="local-file-uploader-box">
                <span class="sub-label">Upload local files:</span>
                <div class="upload-controls-row">
                  <input 
                    type="file" 
                    ref="fileInputRef" 
                    multiple 
                    @change="handleLocalFilesUploaded" 
                    style="display: none;" 
                  />
                  <button type="button" @click="triggerFileInput" class="btn-trigger-upload" :disabled="uploadingFile">
                    {{ uploadingFile ? 'Uploading...' : '📁 Choose Files' }}
                  </button>
                  <span class="upload-tip">Max 50MB per file</span>
                </div>

                <!-- Display uploaded files list -->
                <div class="uploaded-files-chips" v-if="uploadedLocalFiles.length > 0 || selectedExpFiles.length > 0">
                  <div v-for="file in uploadedLocalFiles" :key="file.name" class="uploaded-chip local">
                    <span>📎 {{ truncateFileName(file.name, 16) }} (local)</span>
                    <button type="button" class="btn-remove-chip" @click="removeLocalUploadedFile(file.name)">&times;</button>
                  </div>
                  <div v-for="file in selectedExpFiles" :key="file" class="uploaded-chip referenced">
                    <span>📎 {{ truncateFileName(file, 16) }} (exp)</span>
                    <button type="button" class="btn-remove-chip" @click="removeReferencedFile(file)">&times;</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Priority Checkbox -->
            <div class="checkbox-form-row">
              <label class="checkbox-label-wrapper">
                <input type="checkbox" v-model="formEvent.is_important" />
                <span class="checkbox-custom-text">Mark as high-priority lab milestone (milestones show up in sidebar timeline)</span>
              </label>
            </div>
          </div>

          <div class="modal-actions">
            <button 
              type="button" 
              class="btn-delete-modal" 
              v-if="isEditMode" 
              @click="handleDeleteFromModal"
            >
              Delete Event
            </button>
            <div style="flex: 1;"></div>
            <button type="button" class="btn-cancel" @click="closeEventModal">Cancel</button>
            <button type="submit" class="btn-submit" :disabled="!formEvent.title.trim() || !formEvent.description.trim()">
              Deploy Node
            </button>
          </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Recurrence Saving Prompt Modal -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showRecurrencePrompt" @click.self="closeRecurrencePrompt">
        <div class="modal-box confirmation-modal">
          <div class="modal-header">
            <h3>Modify Recurring Event</h3>
            <button class="btn-close-x" @click="closeRecurrencePrompt">&times;</button>
          </div>
          <div class="confirmation-body">
            <p>You are editing a recurring event series. Do you want to apply these changes to the entire series, or just this occurrence on <strong>{{ selectedInstanceDate }}</strong>?</p>
          </div>
          <div class="modal-actions gap-12">
            <button class="btn-cancel" @click="closeRecurrencePrompt">Cancel</button>
            <button class="btn-submit btn-accent" @click="submitEventWithScope(false)">Just This Occurrence</button>
            <button class="btn-submit" @click="submitEventWithScope(true)">Entire Series</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Recurrence Deleting Prompt Modal -->
    <Teleport to="body">
      <div class="modal-backdrop" v-if="showDeleteRecurrencePrompt" @click.self="closeDeleteRecurrencePrompt">
        <div class="modal-box confirmation-modal">
          <div class="modal-header">
            <h3>Delete Recurring Event</h3>
            <button class="btn-close-x" @click="closeDeleteRecurrencePrompt">&times;</button>
          </div>
          <div class="confirmation-body">
            <p>You are deleting a recurring event series. Do you want to delete only this occurrence on <strong>{{ selectedInstanceDate }}</strong>, or the entire series?</p>
          </div>
          <div class="modal-actions gap-12">
            <button class="btn-cancel" @click="closeDeleteRecurrencePrompt">Cancel</button>
            <button class="btn-submit btn-accent" @click="executeDeleteEvent(false)">Delete This Occurrence</button>
            <button class="btn-submit" @click="executeDeleteEvent(true)">Delete Entire Series</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Lightbox Component for Images -->
    <ImageLightbox 
      :isOpen="lightboxOpen" 
      :imageUrl="lightboxImageUrl" 
      :filename="lightboxFilename" 
      :uploader="lightboxUploader" 
      @close="lightboxOpen = false" 
      @download="handleDownloadFile"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import Header from '../components/layout/Header.vue';
import Sidebar from '../components/layout/Sidebar.vue';
import ImageLightbox from '../components/common/ImageLightbox.vue';
import api from '../services/api';
import { useToast } from '../composables/useToast';

const router = useRouter();
const toast = useToast();

const userName = ref('Researcher');
const userRole = ref('member');
const groups = ref([]);
const currentGroupId = ref(0);

// Calendar active dates
const getSavedDate = () => {
  const saved = sessionStorage.getItem('view_date');
  if (saved) {
    const d = new Date(saved);
    if (!isNaN(d.getTime())) return d;
  }
  return new Date();
};
const selectedDate = ref(getSavedDate());
const calendarMonth = ref(new Date(selectedDate.value.getFullYear(), selectedDate.value.getMonth(), 1));

watch(selectedDate, (newVal) => {
  if (newVal) {
    sessionStorage.setItem('view_date', newVal.toISOString());
  }
});

const jumpToToday = () => {
  const today = new Date();
  selectedDate.value = today;
  calendarMonth.value = new Date(today.getFullYear(), today.getMonth(), 1);
  loadWeekEvents();
};

const selectedDateISO = computed(() => {
  const d = selectedDate.value;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
});

const shiftCalendarMonth = (months) => {
  const d = new Date(calendarMonth.value);
  d.setMonth(d.getMonth() + months);
  calendarMonth.value = d;
};

const calendarMonthYearText = computed(() => {
  const options = { year: 'numeric', month: 'long' };
  return calendarMonth.value.toLocaleDateString('en-US', options);
});

const calendarGridDays = computed(() => {
  const cells = [];
  const year = calendarMonth.value.getFullYear();
  const month = calendarMonth.value.getMonth();
  
  const firstDay = new Date(year, month, 1);
  let dayOfWeek = firstDay.getDay();
  dayOfWeek = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
  
  const prevMonthEnd = new Date(year, month, 0);
  const prevMonthDays = prevMonthEnd.getDate();
  
  for (let i = dayOfWeek - 1; i >= 0; i--) {
    const d = new Date(year, month - 1, prevMonthDays - i);
    cells.push({
      date: d,
      dayNum: d.getDate(),
      isCurrentMonth: false,
      dateStr: formatDateISO(d)
    });
  }
  
  const currentMonthEnd = new Date(year, month + 1, 0);
  const currentMonthDays = currentMonthEnd.getDate();
  for (let i = 1; i <= currentMonthDays; i++) {
    const d = new Date(year, month, i);
    cells.push({
      date: d,
      dayNum: i,
      isCurrentMonth: true,
      dateStr: formatDateISO(d)
    });
  }
  
  const remaining = 42 - cells.length;
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i);
    cells.push({
      date: d,
      dayNum: i,
      isCurrentMonth: false,
      dateStr: formatDateISO(d)
    });
  }
  
  return cells;
});

const formatDateISO = (d) => {
  const yr = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const dy = String(d.getDate()).padStart(2, '0');
  return `${yr}-${mo}-${dy}`;
};

const datesWithEvents = ref({});
const fetchCalendarDots = async () => {
  const cells = calendarGridDays.value;
  if (!cells || cells.length === 0) return;
  const startStr = cells[0].dateStr;
  const endStr = cells[cells.length - 1].dateStr;
  try {
    const res = await api.get(`/events?start_date=${startStr}&end_date=${endStr}`);
    const dotsMap = {};
    res.data.forEach(event => {
      if (event.instance_date) {
        dotsMap[event.instance_date] = true;
      }
    });
    datesWithEvents.value = dotsMap;
  } catch (err) {
    console.error("Failed to load calendar dots:", err);
  }
};

watch(calendarMonth, () => {
  fetchCalendarDots();
}, { immediate: true });

const monthNames = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const yearRange = computed(() => {
  const currentYear = new Date().getFullYear();
  const startYear = currentYear - 10;
  const endYear = currentYear + 10;
  const list = [];
  for (let y = startYear; y <= endYear; y++) {
    list.push(y);
  }
  return list;
});

const onMonthSelectChange = (e) => {
  const newMonth = parseInt(e.target.value, 10);
  const d = new Date(calendarMonth.value);
  d.setMonth(newMonth);
  calendarMonth.value = d;
};

const onYearSelectChange = (e) => {
  const newYear = parseInt(e.target.value, 10);
  const d = new Date(calendarMonth.value);
  d.setFullYear(newYear);
  calendarMonth.value = d;
};

const selectCalendarDate = async (dateObj) => {
  selectedDate.value = dateObj;
  if (dateObj.getMonth() !== calendarMonth.value.getMonth()) {
    calendarMonth.value = new Date(dateObj.getFullYear(), dateObj.getMonth(), 1);
  }
  await loadWeekEvents();
  await nextTick();
  
  const dateStr = formatDateISO(dateObj);
  const element = document.getElementById(`day-section-${dateStr}`);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    element.classList.add('highlight-flash');
    setTimeout(() => {
      element.classList.remove('highlight-flash');
    }, 2000);
  }
};

const isCellInActiveWeek = (dateStr) => {
  const cellDate = new Date(dateStr);
  cellDate.setHours(12,0,0,0);
  
  const mon = new Date(activeMonday.value);
  mon.setHours(0,0,0,0);
  const sun = new Date(activeMonday.value);
  sun.setDate(sun.getDate() + 6);
  sun.setHours(23,59,59,999);
  
  return cellDate >= mon && cellDate <= sun;
};

const isCellSelected = (dateStr) => {
  return dateStr === selectedDateISO.value;
};

const isCellToday = (dateStr) => {
  const today = new Date();
  const yr = today.getFullYear();
  const mo = String(today.getMonth() + 1).padStart(2, '0');
  const dy = String(today.getDate()).padStart(2, '0');
  return dateStr === `${yr}-${mo}-${dy}`;
};

// Calculate Monday of the active week
const activeMonday = computed(() => {
  const d = new Date(selectedDate.value);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(d.setDate(diff));
});

// Format range of the week "YYYY-MM-DD ~ YYYY-MM-DD"
const formatWeekRangeText = computed(() => {
  const start = new Date(activeMonday.value);
  const end = new Date(activeMonday.value);
  end.setDate(end.getDate() + 6);
  
  const formatDate = (d) => {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };
  return `${formatDate(start)} ~ ${formatDate(end)}`;
});

const weeklyDays = ref([]);
const eventsList = ref([]);

// Important Overview events
const importantEvents = computed(() => {
  return eventsList.value.filter(e => e.is_important);
});

// Modal and Form Status
const showEventModal = ref(false);
const isEditMode = ref(false);
const editingEventId = ref(null);
const allExperiments = ref([]);
const allAvailableTags = ref([]);
const customTagInput = ref('');
const expAttachments = ref([]); // Loaded from experiment logs

// Attachments list files
const selectedExpFiles = ref([]); // Referenced experiment files names
const uploadedLocalFiles = ref([]); // Local files list: [{"name": name, "url": url}]
const uploadingFile = ref(false);

const allUsers = ref([]);
const fetchAllUsers = async () => {
  try {
    const res = await api.get('/auth/users');
    allUsers.value = res.data;
  } catch (err) {
    // fail silently
  }
};

const formEvent = ref({
  title: '',
  description: '',
  dateStr: '',
  timeStr: '',
  experiment_id: null,
  tags: [],
  recurrence_rule: null,
  recurrence_end_date_str: '',
  is_important: false,
  participants: []
});

const fileInputRef = ref(null);
const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

// Recurrence confirm state
const showRecurrencePrompt = ref(false);
const showDeleteRecurrencePrompt = ref(false);
const selectedInstanceDate = ref('');
const deleteEventObj = ref(null);

// Comments state
const expandedComments = ref({});
const commentsData = ref({}); // event_id -> list of comments
const loadingComments = ref({});
const commentInputs = ref({});

// Lightbox state
const lightboxOpen = ref(false);
const lightboxImageUrl = ref('');
const lightboxFilename = ref('');
const lightboxUploader = ref('');

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher';
  userRole.value = localStorage.getItem('role') || 'member';
  
  // Load standard parameters
  const storedGroup = localStorage.getItem('activeGroupId');
  if (storedGroup) {
    currentGroupId.value = Number(storedGroup);
  }

  // Fetch latest user profile to bypass stale localstorage role cache
  try {
    const meRes = await api.get('/auth/me');
    userRole.value = meRes.data.role;
    localStorage.setItem('role', meRes.data.role);
    localStorage.setItem('userName', `${meRes.data.first_name} ${meRes.data.last_name}`);
    userName.value = `${meRes.data.first_name} ${meRes.data.last_name}`;
  } catch (err) {
    // Fail silently, fallback to local cache values
  }
  
  await fetchUserGroups();
  await fetchExperiments();
  await fetchSystemTags();
  await fetchAllUsers();
  await loadWeekEvents();
});

const fetchUserGroups = async () => {
  try {
    const res = await api.get('/auth/groups');
    groups.value = res.data;
  } catch (err) {
    toast.error("Failed to sync group communication arrays.");
  }
};

const handleGroupChange = (groupId) => {
  currentGroupId.value = groupId;
  localStorage.setItem('activeGroupId', groupId);
  loadWeekEvents();
};

const fetchExperiments = async () => {
  try {
    const res = await api.get('/experiments');
    allExperiments.value = res.data;
  } catch (err) {
    toast.error("Failed to fetch experiments list.");
  }
};

const fetchSystemTags = async () => {
  try {
    const res = await api.get('/events/tags');
    const tagsMap = {};
    res.data.forEach(t => {
      tagsMap[t.name] = t.id;
    });
    
    // Ensure default tag types meeting, experiment are present
    const defaults = ["会议", "实验", "重要记录", "组会", "设备调试"];
    defaults.forEach(def => {
      if (!tagsMap[def]) {
        tagsMap[def] = Date.now() + Math.random();
      }
    });
    allAvailableTags.value = Object.keys(tagsMap).map(k => ({ id: tagsMap[k], name: k }));
  } catch (err) {
    allAvailableTags.value = [
      { id: 1, name: "会议" },
      { id: 2, name: "实验" },
      { id: 3, name: "重要记录" }
    ];
  }
};

// Date range calculation helper
const getDatesOfCurrentWeek = () => {
  const dates = [];
  const start = new Date(activeMonday.value);
  const dayNames = ["Monday (周一)", "Tuesday (周二)", "Wednesday (周三)", "Thursday (周四)", "Friday (周五)", "Saturday (周六)", "Sunday (周日)"];
  
  for (let i = 0; i < 7; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const yr = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, '0');
    const dy = String(d.getDate()).padStart(2, '0');
    const dateStr = `${yr}-${mo}-${dy}`;
    
    // Check if this matches local current date
    const today = new Date();
    const isToday = today.getFullYear() === yr && (today.getMonth() + 1) === (d.getMonth() + 1) && today.getDate() === d.getDate();
    
    dates.push({
      dateStr,
      dayName: dayNames[i],
      displayDate: `${mo}/${dy}`,
      isToday,
      events: []
    });
  }
  return dates;
};

// Load backend events for the active week
const loadWeekEvents = async () => {
  try {
    const mondayStr = selectedDateISO.value;
    // We send the Monday string, backend returns events matching start_date to start_date + 6 days
    const formattedMon = `${activeMonday.value.getFullYear()}-${String(activeMonday.value.getMonth() + 1).padStart(2, '0')}-${String(activeMonday.value.getDate()).padStart(2, '0')}`;
    const res = await api.get(`/events?start_date=${formattedMon}`);
    
    eventsList.value = res.data;
    
    // Distribute events into week dates
    const days = getDatesOfCurrentWeek();
    
    // Map backend comments counts and initialize expanded state
    days.forEach(day => {
      day.events = eventsList.value.filter(e => e.instance_date === day.dateStr);
      
      // Load comment count for each event
      day.events.forEach(async (e) => {
        try {
          const commentRes = await api.get(`/events/${e.id}/comments`);
          e.commentsCount = commentRes.data.length;
        } catch (err) {
          e.commentsCount = 0;
        }
      });
    });
    
    weeklyDays.value = days;
  } catch (err) {
    toast.error("Failed to load lab weekly schedule.");
  }
};

// Date input switcher
const handleDateInput = (event) => {
  if (event.target.value) {
    selectedDate.value = new Date(event.target.value);
    loadWeekEvents();
  }
};

// Date shifts
const shiftWeek = (days) => {
  const d = new Date(selectedDate.value);
  d.setDate(d.getDate() + days);
  selectedDate.value = d;
  loadWeekEvents();
};

const setTodayWeek = () => {
  selectedDate.value = new Date();
  loadWeekEvents();
};

// Scroll trigger helper
const scrollToEvent = (key) => {
  const card = document.querySelector(`.event-card`); // Find element or display it
  toast.info(`Navigating to event node...`);
};

// Event permissions checks
const canManageEvent = (event) => {
  return userRole.value === 'sys_admin' || event.author_id === Number(localStorage.getItem('userId'));
};

const navigateToExperiment = (id) => {
  router.push(`/experiment/${id}`);
};

const toggleTagSelection = (tagName) => {
  const index = formEvent.value.tags.indexOf(tagName);
  if (index > -1) {
    formEvent.value.tags.splice(index, 1);
  } else {
    formEvent.value.tags.push(tagName);
  }
};

const addCustomTag = () => {
  const tag = customTagInput.value.trim();
  if (tag) {
    if (!formEvent.value.tags.includes(tag)) {
      formEvent.value.tags.push(tag);
    }
    if (!allAvailableTags.value.some(t => t.name === tag)) {
      allAvailableTags.value.push({ id: Date.now(), name: tag });
    }
    customTagInput.value = '';
  }
};

// Load attachments from chosen experiment
const handleExperimentChange = async (keepExistingSelection = false) => {
  const expId = formEvent.value.experiment_id;
  expAttachments.value = [];
  if (keepExistingSelection !== true) {
    selectedExpFiles.value = [];
  }
  
  if (expId) {
    try {
      const res = await api.get(`/experiments/${expId}/logs`);
      const files = [];
      res.data.forEach(log => {
        if (log.attachments) {
          log.attachments.forEach(file => {
            if (!files.includes(file)) {
              files.push(file);
            }
          });
        }
      });
      expAttachments.value = files;
    } catch (err) {
      toast.error("Failed to query experiment log attachments.");
    }
  }
};

// Remove attachments referenced from experiment
const removeReferencedFile = (fileName) => {
  selectedExpFiles.value = selectedExpFiles.value.filter(f => f !== fileName);
};

// Local files upload handler
const handleLocalFilesUploaded = async (e) => {
  const files = e.target.files;
  if (!files || files.length === 0) return;
  
  uploadingFile.value = true;
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      toast.info(`Uploading file [${file.name}] to server node...`);
      const res = await api.post("/events/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      uploadedLocalFiles.value.push({ name: res.data.filename, url: res.data.url });
      toast.success(`Uploaded [${file.name}] successfully.`);
    } catch (err) {
      toast.error(`Upload failed for file [${file.name}]: ${err.response?.data?.detail || err.message}`);
    }
  }
  uploadingFile.value = false;
  // Clear input
  if (e.target) e.target.value = '';
};

const removeLocalUploadedFile = (fileName) => {
  uploadedLocalFiles.value = uploadedLocalFiles.value.filter(f => f.name !== fileName);
};

// Event Dialog Creation
const openCreateModal = (dateStr = null) => {
  isEditMode.value = false;
  editingEventId.value = null;
  uploadedLocalFiles.value = [];
  selectedExpFiles.value = [];
  expAttachments.value = [];
  
  const now = new Date();
  
  // Set default times: start now, end 1 hour later
  const hr = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  
  const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
  const endHr = String(oneHourLater.getHours()).padStart(2, '0');
  const endMin = String(oneHourLater.getMinutes()).padStart(2, '0');
  
  // Clean parameter: if dateStr is an Event object or not a string, treat as null
  let targetDateStr = dateStr;
  if (targetDateStr && (typeof targetDateStr !== 'string' || targetDateStr instanceof Event)) {
    targetDateStr = null;
  }
  
  // Resolve target date string: use parameter, or selected date, or today
  if (!targetDateStr) {
    if (selectedDateISO.value) {
      targetDateStr = selectedDateISO.value;
    } else {
      const yr = now.getFullYear();
      const mo = String(now.getMonth() + 1).padStart(2, '0');
      const dy = String(now.getDate()).padStart(2, '0');
      targetDateStr = `${yr}-${mo}-${dy}`;
    }
  }
  
  formEvent.value = {
    title: '',
    description: '',
    dateStr: targetDateStr,
    timeStr: `${hr}:${min}`,
    endTimeStr: `${endHr}:${endMin}`,
    experiment_id: null,
    tags: [],
    recurrence_rule: null,
    recurrence_end_date_str: '',
    is_important: false,
    participants: []
  };
  showEventModal.value = true;
};

// Edit event click
const openEditModal = (event) => {
  isEditMode.value = true;
  editingEventId.value = event.id;
  selectedInstanceDate.value = event.instance_date;
  
  // Format date and time
  const d = new Date(event.start_date);
  const yr = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const dy = String(d.getDate()).padStart(2, '0');
  const hr = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  
  let endTimeStr = '';
  if (event.end_date) {
    const dEnd = new Date(event.end_date);
    const endHr = String(dEnd.getHours()).padStart(2, '0');
    const endMin = String(dEnd.getMinutes()).padStart(2, '0');
    endTimeStr = `${endHr}:${endMin}`;
  } else {
    const oneHourLater = new Date(d.getTime() + 60 * 60 * 1000);
    const endHr = String(oneHourLater.getHours()).padStart(2, '0');
    const endMin = String(oneHourLater.getMinutes()).padStart(2, '0');
    endTimeStr = `${endHr}:${endMin}`;
  }
  
  // Recurrence end date
  let recurrence_end_date_str = '';
  if (event.recurrence_end_date) {
    const endD = new Date(event.recurrence_end_date);
    recurrence_end_date_str = `${endD.getFullYear()}-${String(endD.getMonth() + 1).padStart(2, '0')}-${String(endD.getDate()).padStart(2, '0')}`;
  }

  // Map attachments
  uploadedLocalFiles.value = [];
  selectedExpFiles.value = [];
  if (event.attachments) {
    event.attachments.forEach(file => {
      if (file.is_referenced) {
        selectedExpFiles.value.push(file.name);
      } else {
        uploadedLocalFiles.value.push({ name: file.name, url: file.url });
      }
    });
  }

  formEvent.value = {
    title: event.title,
    description: event.description,
    dateStr: `${yr}-${mo}-${dy}`, // Default to the selected instance date or base date
    timeStr: `${hr}:${min}`,
    endTimeStr,
    experiment_id: event.experiment_id,
    tags: event.tags.map(t => t.name),
    recurrence_rule: event.recurrence_rule,
    recurrence_end_date_str,
    is_important: event.is_important,
    participants: event.participants ? event.participants.map(p => p.id) : []
  };
  
  // If editing occurrence, set default date input to this occurrence date
  if (event.recurrence_rule) {
    formEvent.value.dateStr = event.instance_date;
  } else {
    formEvent.value.dateStr = `${yr}-${mo}-${dy}`;
  }

  // Load experiment attachments if linked
  handleExperimentChange(true);
  showEventModal.value = true;
};

const closeEventModal = () => {
  showEventModal.value = false;
};

// Submit flow: checks recurrence prompt
const formatEventTimeRange = (startIso, endIso) => {
  if (!startIso) return '';
  const dStart = new Date(startIso);
  const startHrs = String(dStart.getHours()).padStart(2, '0');
  const startMins = String(dStart.getMinutes()).padStart(2, '0');
  const startStr = `${startHrs}:${startMins}`;
  
  if (!endIso) return startStr;
  
  const dEnd = new Date(endIso);
  const endHrs = String(dEnd.getHours()).padStart(2, '0');
  const endMins = String(dEnd.getMinutes()).padStart(2, '0');
  const endStr = `${endHrs}:${endMins}`;
  
  const dStartDateStr = dStart.toDateString();
  const dEndDateStr = dEnd.toDateString();
  if (dStartDateStr !== dEndDateStr) {
    const startMonth = dStart.getMonth() + 1;
    const startDate = dStart.getDate();
    const endMonth = dEnd.getMonth() + 1;
    const endDate = dEnd.getDate();
    return `${startMonth}/${startDate} ${startStr} - ${endMonth}/${endDate} ${endStr}`;
  }
  
  return `${startStr} - ${endStr}`;
};

const checkIfOnlyAttachmentsChanged = (orig, formVal) => {
  if (!orig) return false;
  
  const titleChanged = orig.title !== formVal.title;
  const descChanged = orig.description !== formVal.description;
  const expChanged = orig.experiment_id !== formVal.experiment_id;
  const importantChanged = orig.is_important !== formVal.is_important;
  const ruleChanged = orig.recurrence_rule !== formVal.recurrence_rule;
  
  const d = new Date(orig.start_date);
  const origTimeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  const timeChanged = origTimeStr !== formVal.timeStr;
  
  let endTimeChanged = false;
  if (orig.end_date) {
    const dEnd = new Date(orig.end_date);
    const origEndTimeStr = `${String(dEnd.getHours()).padStart(2, '0')}:${String(dEnd.getMinutes()).padStart(2, '0')}`;
    endTimeChanged = origEndTimeStr !== formVal.endTimeStr;
  } else {
    endTimeChanged = !!formVal.endTimeStr;
  }
  
  const dateChanged = orig.instance_date ? (orig.instance_date !== formVal.dateStr) : false;

  const origTags = (orig.tags || []).map(t => t.name).sort().join(',');
  const formTags = [...(formVal.tags || [])].sort().join(',');
  const tagsChanged = origTags !== formTags;

  const origParts = (orig.participants || []).map(p => p.id).sort().join(',');
  const formParts = [...(formVal.participants || [])].sort().join(',');
  const participantsChanged = origParts !== formParts;

  let origEndStr = '';
  if (orig.recurrence_end_date) {
    const endD = new Date(orig.recurrence_end_date);
    origEndStr = `${endD.getFullYear()}-${String(endD.getMonth() + 1).padStart(2, '0')}-${String(endD.getDate()).padStart(2, '0')}`;
  }
  const endChanged = origEndStr !== formVal.recurrence_end_date_str;

  const fieldsChanged = titleChanged || descChanged || expChanged || importantChanged || ruleChanged || timeChanged || endTimeChanged || dateChanged || tagsChanged || participantsChanged || endChanged;
  
  return !fieldsChanged;
};

const handleSubmitEvent = () => {
  if (isEditMode.value) {
    const originalEvent = eventsList.value.find(e => e.id === editingEventId.value);
    const isRecurring = originalEvent && (originalEvent.recurrence_rule || originalEvent.parent_event_id);
    
    if (isRecurring) {
      const onlyAttachments = checkIfOnlyAttachmentsChanged(originalEvent, formEvent.value);
      if (onlyAttachments) {
        // Default to modifying only this occurrence for attachments changes without prompting
        submitEventWithScope(false);
      } else {
        showRecurrencePrompt.value = true;
      }
      return;
    }
  }
  
  // Standalone event creation or saving
  submitEventWithScope(true);
};

const closeRecurrencePrompt = () => {
  showRecurrencePrompt.value = false;
};

// Execution update
const submitEventWithScope = async (modifySeries) => {
  showRecurrencePrompt.value = false;
  
  // Format final attachments payload
  const finalAttachments = [];
  selectedExpFiles.value.forEach(fileName => {
    finalAttachments.push({
      name: fileName,
      url: `/experiments/attachments/${fileName}`,
      is_referenced: true
    });
  });
  
  uploadedLocalFiles.value.forEach(file => {
    finalAttachments.push({
      name: file.name,
      url: file.url,
      is_referenced: false
    });
  });
  
  // Combine date and time
  const startDateTimeStr = `${formEvent.value.dateStr}T${formEvent.value.timeStr}:00`;
  
  let endDateTimeStr = null;
  if (formEvent.value.endTimeStr) {
    endDateTimeStr = `${formEvent.value.dateStr}T${formEvent.value.endTimeStr}:00`;
    if (formEvent.value.endTimeStr < formEvent.value.timeStr) {
      const d = new Date(startDateTimeStr);
      d.setDate(d.getDate() + 1);
      const nextDayStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      endDateTimeStr = `${nextDayStr}T${formEvent.value.endTimeStr}:00`;
    }
  }
  
  let recurrence_end_date = null;
  if (formEvent.value.recurrence_rule && formEvent.value.recurrence_end_date_str) {
    recurrence_end_date = `${formEvent.value.recurrence_end_date_str}T23:59:59`;
  }

  const payload = {
    title: formEvent.value.title,
    description: formEvent.value.description,
    experiment_id: formEvent.value.experiment_id,
    start_date: startDateTimeStr,
    end_date: endDateTimeStr,
    is_important: formEvent.value.is_important,
    attachments: finalAttachments,
    recurrence_rule: formEvent.value.recurrence_rule,
    recurrence_end_date,
    tags: formEvent.value.tags,
    participants: formEvent.value.participants
  };

  try {
    if (isEditMode.value) {
      let url = `/events/${editingEventId.value}?modify_series=${modifySeries}`;
      if (!modifySeries) {
        url += `&instance_date=${selectedInstanceDate.value}`;
      }
      await api.put(url, payload);
      toast.success("Lab Event node updated successfully.");
    } else {
      await api.post('/events', payload);
      toast.success("Lab Event node created successfully.");
    }
    showEventModal.value = false;
    await loadWeekEvents();
    fetchCalendarDots();
  } catch (err) {
    toast.error(err.response?.data?.detail || "Failed to commit Event node updates.");
  }
};

// Deletion flow
const confirmDeleteEvent = (event) => {
  deleteEventObj.value = event;
  selectedInstanceDate.value = event.instance_date;
  if (event.recurrence_rule || event.parent_event_id) {
    showDeleteRecurrencePrompt.value = true;
  } else {
    // Delete standalone directly
    executeDeleteEvent(true);
  }
};

const handleDeleteFromModal = () => {
  showEventModal.value = false;
  const originalEvent = eventsList.value.find(
    e => e.id === editingEventId.value && e.instance_date === selectedInstanceDate.value
  );
  if (originalEvent) {
    confirmDeleteEvent(originalEvent);
  }
};

const closeDeleteRecurrencePrompt = () => {
  showDeleteRecurrencePrompt.value = false;
  deleteEventObj.value = null;
};

const executeDeleteEvent = async (deleteSeries) => {
  showDeleteRecurrencePrompt.value = false;
  const event = deleteEventObj.value;
  if (!event) return;

  try {
    let url = '';
    if (deleteSeries) {
      // Delete the entire series
      const targetId = event.parent_event_id || event.id;
      url = `/events/${targetId}?delete_series=true`;
    } else {
      // Delete only this occurrence
      if (event.parent_event_id) {
        // It's a modified occurrence (child event)
        url = `/events/${event.id}?delete_series=false`;
      } else {
        // It's an unmodified occurrence of a recurring series (or standalone)
        url = `/events/${event.id}?delete_series=false&instance_date=${selectedInstanceDate.value}`;
      }
    }
    await api.delete(url);
    toast.success("Event node deleted from workspace.");
    await loadWeekEvents();
    fetchCalendarDots();
  } catch (err) {
    toast.error("Failed to delete the chosen event.");
  } finally {
    deleteEventObj.value = null;
  }
};

// Comments Management
const toggleComments = async (event) => {
  const key = event.unique_key;
  if (expandedComments.value[key]) {
    expandedComments.value[key] = false;
  } else {
    expandedComments.value[key] = true;
    commentInputs.value[key] = '';
    
    // Load comments
    loadingComments.value[key] = true;
    try {
      const res = await api.get(`/events/${event.id}/comments`);
      commentsData.value[event.id] = res.data;
    } catch (err) {
      toast.error("Failed to sync comments for this event.");
    }
    loadingComments.value[key] = false;
  }
};

const submitComment = async (event) => {
  const key = event.unique_key;
  const content = commentInputs.value[key]?.trim();
  if (!content) return;

  try {
    const res = await api.post(`/events/${event.id}/comments`, { content });
    if (!commentsData.value[event.id]) {
      commentsData.value[event.id] = [];
    }
    commentsData.value[event.id].push(res.data);
    commentInputs.value[key] = '';
    event.commentsCount = (event.commentsCount || 0) + 1;
    toast.success("Comment added.");
  } catch (err) {
    toast.error("Failed to add comment.");
  }
};

// Attachments Handling
const handleAttachmentClick = (filename, uploader) => {
  if (!filename) return;
  const lowercaseName = filename.toLowerCase();
  const token = localStorage.getItem('token') || '';
  
  if (lowercaseName.endsWith('.pdf')) {
    const url = `${api.defaults.baseURL}/events/attachments/${filename}?preview=true&token=${token}`;
    window.open(url, '_blank');
    toast.info(`📖 Opening PDF preview [${truncateFileName(filename, 16)}] in new tab...`);
  } else if (/\.(png|jpe?g|gif|webp)$/i.test(lowercaseName)) {
    lightboxFilename.value = filename;
    lightboxUploader.value = uploader;
    lightboxImageUrl.value = `${api.defaults.baseURL}/events/attachments/${filename}?preview=true&token=${token}`;
    lightboxOpen.value = true;
  } else {
    handleDownloadFile(filename);
  }
};

const handleDownloadFile = (filename) => {
  if (!filename) return;
  toast.info(`💾 Retrieving [${truncateFileName(filename, 16)}] bits from central repository...`);
  
  api.get(`/events/attachments/${filename}`, { responseType: 'blob' })
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
      toast.error("File download failed. Check permissions.");
    });
};

const handleLogout = () => {
  localStorage.clear();
  router.push('/login');
};

// Formats utilities
const truncateFileName = (name, length = 20) => {
  if (!name) return '';
  if (name.length <= length) return name;
  const extIndex = name.lastIndexOf('.');
  
  if (extIndex === -1) {
    const half = Math.floor((length - 3) / 2);
    return name.slice(0, half) + '...' + name.slice(name.length - half);
  }
  
  const ext = name.slice(extIndex);
  const base = name.slice(0, extIndex);
  const baseLen = length - ext.length - 3;
  
  if (baseLen > 4) {
    const half = Math.floor(baseLen / 2);
    return base.slice(0, half) + '...' + base.slice(base.length - (baseLen - half)) + ext;
  }
  
  const half = Math.floor((length - 3) / 2);
  return name.slice(0, half) + '...' + name.slice(name.length - half);
};

const formatTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

const formatRecurrenceText = (rule) => {
  if (!rule) return 'None';
  const mapping = {
    'weekly': 'Weekly (每星期)',
    'biweekly': 'Bi-weekly (每两星期)',
    'monthly': 'Monthly (每月)'
  };
  return mapping[rule.toLowerCase()] || rule;
};

const getRecurrenceTooltip = (event) => {
  let text = `Repeats ${event.recurrence_rule}`;
  if (event.recurrence_end_date) {
    text += ` until ${new Date(event.recurrence_end_date).toLocaleDateString()}`;
  } else {
    text += ' indefinitely';
  }
  return text;
};

const getTagColorClass = (name) => {
  const map = {
    "会议": "badge-meeting",
    "实验": "badge-experiment",
    "组会": "badge-meeting",
    "设备调试": "badge-debug",
    "重要记录": "badge-milestone"
  };
  return map[name] || "badge-default";
};
</script>

<style scoped>
.dashboard-layout { height: 100%; overflow: hidden; background-color: var(--bg-primary); }
.main-content {
  margin-top: 64px;
  margin-left: 240px;
  padding: 24px 32px;
  box-sizing: border-box;
  height: calc(100vh - 64px);
  overflow: hidden;
}
.workspace-container {
  display: flex;
  gap: 28px;
  max-width: 1400px;
  margin: 0 auto;
  align-items: stretch;
  height: 100%;
}
.workspace-left {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  padding-right: 4px;
}
.workspace-right {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
}
.workspace-right::-webkit-scrollbar {
  width: 6px;
}
.workspace-right::-webkit-scrollbar-track {
  background: transparent;
}
.workspace-right::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.workspace-right::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.timeline-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff !important;
  border: 1px solid var(--border);
  padding: 16px 24px;
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.header-title-zone {
  text-align: left;
}

.view-pill {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 4px 10px;
  border-radius: 99px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.header-title-zone h2 {
  font-size: 20px;
  margin: 6px 0 0 0;
  font-weight: 700;
  color: var(--text-h);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-nav-week {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-nav-week:hover {
  background: #f8fafc;
  color: var(--text-h);
  border-color: #cbd5e1;
}

.btn-create-event {
  background: linear-gradient(135deg, var(--accent), #7c3aed);
  border: none;
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
  transition: all 0.15s ease;
}

.btn-create-event:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.35);
}

/* Weekly Timeline Days List */
.weekly-timeline-flow {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}

.weekly-timeline-flow::-webkit-scrollbar {
  width: 6px;
}
.weekly-timeline-flow::-webkit-scrollbar-track {
  background: transparent;
}
.weekly-timeline-flow::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.weekly-timeline-flow::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.timeline-day-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--border);
  border-radius: 16px;
  transition: all 0.2s ease;
}

.timeline-day-section.is-today {
  border-color: var(--accent);
  background: linear-gradient(180deg, rgba(170, 59, 255, 0.02) 0%, rgba(255, 255, 255, 0.6) 100%);
  box-shadow: 0 4px 20px -2px rgba(170, 59, 255, 0.06);
}

.timeline-day-section.highlight-flash {
  animation: day-highlight-pulse 2s ease;
}

@keyframes day-highlight-pulse {
  0% {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px rgba(170, 59, 255, 0.2), 0 4px 12px rgba(170, 59, 255, 0.1) !important;
    background: rgba(170, 59, 255, 0.05) !important;
  }
  50% {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 6px rgba(170, 59, 255, 0.3), 0 6px 16px rgba(170, 59, 255, 0.15) !important;
    background: rgba(170, 59, 255, 0.08) !important;
  }
  100% {
    box-shadow: none !important;
  }
}

.day-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-align: left;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}

.day-indicator-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.day-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-h);
}

.day-date {
  font-size: 13px;
  color: var(--text);
  font-family: var(--mono);
}

.today-badge {
  font-size: 9px;
  font-weight: 800;
  background: var(--accent);
  color: #ffffff;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.day-events-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.no-events-placeholder {
  font-size: 12.5px;
  color: var(--text);
  font-style: italic;
  padding: 12px 6px;
  text-align: left;
}

/* Event Card Design */
.event-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
  text-align: left;
}

.event-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.event-card.is-important-card {
  border-left: 4px solid #f97316;
}

.event-card-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 10px;
}

.event-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-tags-row {
  display: flex;
  gap: 6px;
}

.event-tag-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 99px;
}

.badge-meeting { background: #dbeafe; color: #1e40af; }
.badge-experiment { background: #dcfce7; color: #15803d; }
.badge-debug { background: #fef9c3; color: #854d0e; }
.badge-milestone { background: #ffedd5; color: #c2410c; }
.badge-default { background: #f1f5f9; color: #475569; }

.important-chip {
  font-size: 10px;
  font-weight: 700;
  background: #ffedd5;
  color: #ea580c;
  padding: 2px 8px;
  border-radius: 99px;
  border: 1px solid #fed7aa;
}

.event-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.event-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-h);
  margin: 2px 0 0 0;
}

.event-card-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: transparent;
  border: none;
  font-size: 14px;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s;
}

.action-btn:hover {
  background: #f1f5f9;
}

.event-author-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  color: #64748b;
  margin-top: 4px;
}

.author-name {
  font-weight: 600;
  color: #334155;
}

.exp-link-badge {
  background: #f1f5f9;
  color: #1e293b;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.exp-link-badge:hover {
  background: #e2e8f0;
  color: var(--accent);
}

.recurrence-badge {
  background: #faf5ff;
  border: 1px solid #f3e8ff;
  color: #6b21a8;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}

/* Event Card Body (Introduction + Attachments) */
.event-body {
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.event-description {
  font-size: 13.5px;
  line-height: 1.5;
  color: #334155;
  white-space: pre-wrap;
  margin: 0 0 12px 0;
}

.event-attachments-section {
  text-align: left;
}

.attachments-title {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.attachments-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.attach-name-link {
  color: #1d4ed8;
  font-weight: 600;
  cursor: pointer;
}

.attach-name-link:hover {
  text-decoration: underline;
}

.attach-source-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
}

.attach-source-badge.ref-source {
  background: #e0f2fe;
  color: #0369a1;
}

.attach-source-badge.upload-source {
  background: #ede9fe;
  color: #6d28d9;
}

.event-card-footer {
  padding-top: 8px;
  display: flex;
}

.btn-toggle-comments {
  background: transparent;
  border: none;
  font-size: 12.5px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.btn-toggle-comments:hover {
  background: #f1f5f9;
  color: var(--text-h);
}

.arrow-indicator {
  font-size: 9px;
  color: #94a3b8;
}

/* Event Comments Drawer */
.event-comments-drawer {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
  margin-top: 10px;
  border: 1px solid #e2e8f0;
}

.comments-list-wrapper {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.comments-loading,
.empty-comments {
  font-size: 12px;
  color: #64748b;
  font-style: italic;
  padding: 8px 0;
  text-align: center;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comment-item {
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 8px;
}

.comment-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.comment-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 2px;
}

.comment-author {
  font-weight: 600;
  color: #334155;
}

.comment-time {
  font-family: var(--mono);
}

.comment-text {
  font-size: 12.5px;
  color: #334155;
  margin: 0;
  text-align: left;
  padding-left: 20px; /* Indentation! 不顶格写 */
}

.post-comment-form {
  display: flex;
  gap: 8px;
}

.comment-input-field {
  flex: 1;
  padding: 6px 12px;
  font-size: 12.5px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  outline: none;
  background: #ffffff;
}

.comment-input-field:focus {
  border-color: var(--accent);
}

.btn-post-comment {
  background: var(--accent);
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}

.btn-post-comment:disabled {
  background: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
}

/* Right Sidebar Styling */
.calendar-widget-card,
.important-events-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow);
  padding: 16px;
  text-align: left;
}

.calendar-widget-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.widget-subtitle {
  font-size: 12px;
  color: #64748b;
}

.datepicker-wrapper {
  position: relative;
  width: 100%;
}

.datepicker-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 13.5px;
  font-weight: 600;
  color: #1e293b;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  outline: none;
  cursor: pointer;
  box-sizing: border-box;
}

.datepicker-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(170, 59, 255, 0.12);
}

.quick-nav-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.btn-quick-nav {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}

.btn-quick-nav:hover {
  background: #e2e8f0;
  color: var(--text-h);
}

.important-events-body {
  max-height: 380px;
  overflow-y: auto;
}

.empty-important-state {
  font-size: 12px;
  color: #94a3b8;
  font-style: italic;
  padding: 16px 0;
  text-align: center;
}

.important-timeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 4px;
}

.important-timeline-item {
  display: flex;
  gap: 14px;
  border-left: 2px solid #e2e8f0;
  padding-left: 14px;
  position: relative;
  margin-left: 6px;
  padding-bottom: 14px;
  cursor: pointer;
}

.important-timeline-item:last-child {
  border-left: none;
  padding-bottom: 0;
}

.item-indicator-dot {
  position: absolute;
  left: -5px;
  top: 5px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f97316;
  border: 2px solid #ffffff;
  transition: all 0.2s ease;
}

.important-timeline-item:hover .item-indicator-dot {
  transform: scale(1.2);
}

.item-content-box {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.item-date-badge {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 600;
  font-family: var(--mono);
}

.item-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin: 2px 0 4px 0;
}

.item-tags {
  display: flex;
  gap: 4px;
}

.mini-tag {
  font-size: 9px;
  font-weight: 700;
  background: #f1f5f9;
  color: #475569;
  padding: 1px 4px;
  border-radius: 3px;
}

/* Modal Form Styles overrides */
.modal-box.event-modal {
  width: 95%;
  max-width: 580px;
}

.modal-form-row {
  display: flex;
  gap: 12px;
}

.flex-1 {
  flex: 1;
}

.modal-select-input {
  width: 100%;
}

.tag-selector-chip-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.tag-selector-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 99px;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.15s;
}

.tag-selector-pill:hover {
  background: #e2e8f0;
}

.tag-selector-pill.selected {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
}

.custom-tag-adder {
  display: flex;
  gap: 8px;
}

.custom-tag-input {
  flex: 1;
}

.exp-attachments-selector {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 10px;
  background: #f8fafc;
  margin-bottom: 10px;
  text-align: left;
}

.sub-label {
  font-size: 11.5px;
  font-weight: 700;
  color: #475569;
  display: block;
  margin-bottom: 6px;
}

.checkbox-options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  max-height: 120px;
  overflow-y: auto;
}

.checkbox-option-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  
  /* 建议加上以下两行，让卡片有内边距和固定高度，撑起好看的轻灰色卡片 */
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.checkbox-text {
  font-size: 12px;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-alert-text {
  font-size: 11px;
  color: #64748b;
  font-style: italic;
  text-align: left;
  margin-bottom: 10px;
}

.local-file-uploader-box {
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  text-align: left;
  background: #ffffff;
}

.upload-controls-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-trigger-upload {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}

.btn-trigger-upload:hover {
  background: #f1f5f9;
}

.upload-tip {
  font-size: 11px;
  color: #94a3b8;
}

.uploaded-files-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.uploaded-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid;
}

.uploaded-chip.local {
  background: #f5f3ff;
  border-color: #ddd6fe;
  color: #6d28d9;
}

.uploaded-chip.referenced {
  background: #f0f9ff;
  border-color: #bae6fd;
  color: #0369a1;
}

.btn-remove-chip {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #94a3b8;
}

.btn-remove-chip:hover {
  color: #ef4444;
}

.checkbox-form-row {
  text-align: left;
  margin-top: 6px;
}

.checkbox-label-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
}

.checkbox-custom-text {
  font-size: 12px;
  line-height: 1.4;
  color: #475569;
}

/* Confirmation modal tweaks */
.modal-box.confirmation-modal {
  max-width: 440px;
  text-align: left;
}

.confirmation-body {
  font-size: 13.5px;
  line-height: 1.5;
  color: #334155;
  padding: 10px 0 20px 0;
}

.btn-accent {
  background: #7c3aed !important;
}

.btn-accent:hover {
  background: #6d28d9 !important;
}

.gap-12 {
  gap: 12px;
}

/* ==========================================================================
   模态弹窗与表单样式 (Modal Backdrop & Box Styles)
   ========================================================================== */
.modal-backdrop {
  position: fixed !important;
  top: 0 !important; left: 0 !important;
  width: 100vw !important; height: 100vh !important;
  background: rgba(15, 23, 42, 0.45) !important; /* 电影级微暗遮罩 */
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  z-index: var(--z-overlay, 1000) !important; /* 使用 z-index 变量体系中的遮罩层级 */
}

.modal-box {
  background: #ffffff !important;
  border-radius: 14px !important;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 10px 10px -5px rgba(0, 0, 0, 0.03) !important;
  padding: 28px !important;
  box-sizing: border-box !important;
  animation: modal-slide-up 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-slide-up {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.3px;
}

.btn-close-x {
  background: transparent; border: none; font-size: 22px;
  color: #94a3b8; cursor: pointer; padding: 0; line-height: 1;
}

.btn-close-x:hover { color: #475569; }

.modal-form-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-form-group {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.modal-form-group label {
  font-size: 12.5px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.modal-form-group input:not([type="checkbox"]), 
.modal-form-group textarea,
.modal-form-group select {
  padding: 10px 14px !important;
  font-size: 13.5px !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 8px !important;
  outline: none !important;
  background: #ffffff !important;
  color: #1e293b !important;
  box-sizing: border-box !important;
  transition: all 0.15s ease;
}

.modal-form-group input:not([type="checkbox"]):focus,
.modal-form-group textarea:focus,
.modal-form-group select:focus {
  border-color: #2563eb !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.btn-cancel {
  padding: 8px 16px !important;
  background: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 6px !important;
  color: #475569 !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  cursor: pointer !important;
  transition: all 0.1s;
}

.btn-cancel:hover {
  background: #f1f5f9 !important;
  color: #0f172a !important;
}

.btn-submit {
  padding: 8px 18px !important;
  background: #2563eb !important;
  color: white !important;
  border: none !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  cursor: pointer !important;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15) !important;
  transition: all 0.1s;
}

.btn-submit:hover:not(:disabled) {
  background: #1d4ed8 !important;
}

.btn-submit:disabled {
  background: #f1f5f9 !important;
  color: #cbd5e1 !important;
  cursor: not-allowed !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
}

/* ==========================================================================
   Month Calendar Grid Styles
   ========================================================================== */
.calendar-month-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.calendar-month-year-selects {
  display: inline-flex !important;
  align-items: center !important;
  gap: 2px !important;
}

.calendar-select {
  font-size: 13.5px !important;
  font-weight: 700 !important;
  color: #0f172a !important;
  background: transparent !important;
  border: none !important;
  outline: none !important;
  cursor: pointer !important;
  padding: 4px 6px !important;
  border-radius: 6px !important;
  transition: all 0.15s ease !important;
  font-family: inherit !important;
  text-align: center !important;
  text-align-last: center !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
}

.calendar-select::-ms-expand {
  display: none !important;
}

.calendar-select:hover {
  background: #e2e8f0 !important;
  color: var(--accent) !important;
}

.btn-month-nav {
  background: transparent;
  border: none;
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  color: #64748b;
  transition: all 0.15s;
}

.btn-month-nav:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.calendar-days-grid-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.calendar-days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.calendar-day-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
  background: transparent;
  color: #334155;
  position: relative !important;
}

.calendar-day-dot {
  position: absolute !important;
  bottom: 4px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  width: 4px !important;
  height: 4px !important;
  background-color: var(--accent) !important;
  border-radius: 50% !important;
  display: block !important;
}

.calendar-day-cell.selected-day .calendar-day-dot {
  background-color: #ffffff !important;
}

.calendar-day-cell.other-month {
  color: #cbd5e1;
}

.calendar-day-cell:hover {
  background: #f1f5f9;
}

.calendar-day-cell.in-active-week {
  background: rgba(170, 59, 255, 0.08);
  color: var(--accent);
}

.calendar-day-cell.selected-day {
  background: var(--accent) !important;
  color: #ffffff !important;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(170, 59, 255, 0.3);
}

.calendar-day-cell.today-day {
  border: 1px dashed var(--accent);
}

/* ==========================================================================
   Participants Chip Selectors and Badge Styles
   ========================================================================== */
.participants-checkbox-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  max-height: 120px;
  overflow-y: auto;
  margin-top: 4px;
}

.participant-checkbox-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
  color: #475569;
}

.participant-checkbox-item.checked {
  background: var(--accent-bg);
  border-color: var(--accent-border);
  color: var(--accent);
  font-weight: 600;
}

.participant-checkbox-input {
  display: none;
}

.event-participants-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--text-muted);
}

.participants-label {
  font-weight: 700;
  color: var(--text-main);
  margin-right: 4px;
}

.participant-badge {
  background: #f1f5f9;
  color: #475569;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

/* ==========================================================================
   Event Dialog Scroll Layout and Reference Attachments Grid
   ========================================================================== */
.event-modal {
  width: 92% !important;
  max-width: 620px !important;
  max-height: 90vh !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 24px !important;
}

.event-form-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  height: calc(100% - 40px);
}

.modal-form-scroll-wrapper {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 10px;
  margin-bottom: 16px;
}

/* Custom Scrollbar for Modal Scroll Wrapper */
.modal-form-scroll-wrapper::-webkit-scrollbar {
  width: 6px;
}
.modal-form-scroll-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}
.modal-form-scroll-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.modal-form-scroll-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Reference Attachments Grid */
.checkbox-options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 8px;
  margin-top: 6px;
}

.checkbox-option-item {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  padding: 8px 12px !important;
  background: #f8fafc !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 6px !important;
  font-size: 11.5px !important;
  cursor: pointer !important;
  user-select: none !important;
  height: 38px !important;
  box-sizing: border-box !important;
  color: #475569 !important;
  transition: all 0.15s ease !important;
  overflow: hidden !important;
}

.checkbox-option-item:hover {
  background: #f1f5f9;
}

.checkbox-option-item.checked-item {
  background: var(--accent-bg) !important;
  border-color: var(--accent-border) !important;
  color: var(--accent) !important;
  font-weight: 600;
}

.ref-attachment-input {
  width: 16px !important;
  height: 16px !important;
  margin: 0 !important;
  flex-shrink: 0 !important;
  accent-color: var(--accent) !important;
}

.ref-attachment-text {
  flex: 1 !important;
  min-width: 0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  text-align: left !important;
  margin-left: 8px !important;
  color: inherit !important;
}

.event-time-range-row {
  margin-top: 6px;
  margin-bottom: 2px;
  text-align: left;
}

.time-range-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.card-edit-button {
  background: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 6px !important;
  color: #475569 !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 4px 10px !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.card-edit-button:hover {
  background: #f1f5f9 !important;
  border-color: #94a3b8 !important;
  color: #1e293b !important;
}

.btn-delete-modal {
  padding: 8px 16px !important;
  background: #fef2f2 !important;
  border: 1px solid #fee2e2 !important;
  border-radius: 6px !important;
  color: #dc2626 !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.btn-delete-modal:hover {
  background: #fee2e2 !important;
  border-color: #fca5a5 !important;
  color: #b91c1c !important;
}

.month-center-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-today {
  background: #f1f5f9 !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
  color: #475569 !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 4px 10px !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.btn-today:hover {
  background: #e2e8f0 !important;
  color: #0f172a !important;
  border-color: #cbd5e1 !important;
}

.btn-day-add-event {
  background: #eff6ff !important;
  border: 1px solid #dbeafe !important;
  border-radius: 4px !important;
  color: #2563eb !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 4px 10px !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.btn-day-add-event:hover {
  background: #dbeafe !important;
  border-color: #bfdbfe !important;
  color: #1d4ed8 !important;
}
</style>
