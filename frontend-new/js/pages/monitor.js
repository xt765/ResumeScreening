/**
 * 系统监控页面模块
 * 提供日志查看、健康检查功能
 *
 * 设计原则：
 * - 移除任务相关功能，专注于日志查看和系统健康监控
 * - 时间范围快捷选择，提升用户体验
 * - 日志详情可展开查看
 */

const MonitorPage = {
    /** 当前激活的 Tab */
    currentTab: 'logs',

    /** 健康检查数据 */
    healthData: null,

    /** 日志数据 */
    logsData: null,

    /** ECharts 图表实例 */
    charts: {},

    /** 是否正在刷新 */
    isRefreshing: false,

    /** 日志排序方式：desc=逆序（最新在前），asc=正序（最早在前） */
    logSortOrder: 'desc',

    /** 当前日志页码 */
    currentLogPage: 1,

    /** 展开的日志 ID 集合 */
    expandedLogs: new Set(),

    /** 选中的日志级别 */
    selectedLevels: ['DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'],

    /** 当前时间范围快捷选项 */
    currentTimeRange: 'today',

    /** 自定义时间范围 */
    customTimeRange: {
        start: null,
        end: null
    },

    /** 搜索关键词 */
    searchKeyword: '',

    /**
     * 渲染页面
     */
    async render() {
        this.loadHealthData();
        return this.renderContent();
    },

    /**
     * 加载健康检查数据
     */
    async loadHealthData() {
        const healthSection = document.getElementById('healthSection');
        if (healthSection) {
            healthSection.innerHTML = this.renderHealthLoading();
        }

        try {
            const response = await monitorApi.getHealth();
            this.healthData = response.data;
            this.updateHealthUI();
        } catch (error) {
            console.error('加载健康数据失败:', error);
            if (healthSection) {
                healthSection.innerHTML = this.renderHealthError();
            }
        }
    },

    /**
     * 更新健康检查 UI
     */
    updateHealthUI() {
        const healthSection = document.getElementById('healthSection');
        if (healthSection && this.healthData) {
            healthSection.innerHTML = this.renderHealthSection();
            this.initCharts();
        }
    },

    /**
     * 渲染页面内容
     */
    renderContent() {
        return `
            <div class="monitor-page">
                <div class="health-section" id="healthSection">
                    ${this.renderHealthLoading()}
                </div>

                <div class="logs-section" id="logsSection">
                    ${this.renderLogsSection()}
                </div>
            </div>
        `;
    },

    /**
     * 渲染健康检查加载状态
     */
    renderHealthLoading() {
        return `
            <div class="health-loading">
                <div class="loading-spinner"></div>
                <span>正在获取系统状态...</span>
            </div>
        `;
    },

    /**
     * 渲染健康检查错误状态
     */
    renderHealthError() {
        return `
            <div class="health-error">
                <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <div class="error-text">无法获取系统状态</div>
                <button class="btn btn-primary" onclick="MonitorPage.loadHealthData()">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="23 4 23 10 17 10"/>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                    </svg>
                    重试
                </button>
            </div>
        `;
    },

    /**
     * 渲染健康检查区域
     */
    renderHealthSection() {
        const data = this.healthData || {};
        const resources = data.resources || {};
        const services = data.services || [];

        return `
            <div class="health-grid">
                <!-- 资源监控卡片 -->
                <div class="health-card resource-card">
                    <div class="card-header-row">
                        <h3 class="card-title">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                                <line x1="8" y1="21" x2="16" y2="21"/>
                                <line x1="12" y1="17" x2="12" y2="21"/>
                            </svg>
                            资源监控
                        </h3>
                        <button class="btn btn-primary btn-sm refresh-btn" id="refreshHealthBtn" onclick="MonitorPage.handleRefreshHealth()">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="23 4 23 10 17 10"/>
                                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                            </svg>
                            立即检查
                        </button>
                    </div>
                    <div class="resource-gauges">
                        <div class="gauge-item">
                            <div class="gauge-chart" id="cpuGauge"></div>
                            <div class="gauge-info">
                                <div class="gauge-label">CPU 使用率</div>
                            </div>
                        </div>
                        <div class="gauge-item">
                            <div class="gauge-chart" id="memoryGauge"></div>
                            <div class="gauge-info">
                                <div class="gauge-label">内存使用率</div>
                                <div class="gauge-detail">${resources.memory_used_gb || 0} / ${resources.memory_total_gb || 0} GB</div>
                            </div>
                        </div>
                        <div class="gauge-item">
                            <div class="gauge-chart" id="diskGauge"></div>
                            <div class="gauge-info">
                                <div class="gauge-label">磁盘使用率</div>
                                <div class="gauge-detail">${resources.disk_used_gb || 0} / ${resources.disk_total_gb || 0} GB</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 服务状态卡片 -->
                <div class="health-card services-card">
                    <div class="card-header-row">
                        <h3 class="card-title">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                            </svg>
                            服务状态
                        </h3>
                        <span class="services-summary">${this.getServicesSummary(services)}</span>
                    </div>
                    <div class="services-grid">
                        ${services.map(s => this.renderServiceItem(s)).join('')}
                    </div>
                </div>

                <!-- 系统信息卡片 -->
                <div class="health-card system-card">
                    <div class="card-header-row">
                        <h3 class="card-title">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="12" y1="16" x2="12" y2="12"/>
                                <line x1="12" y1="8" x2="12.01" y2="8"/>
                            </svg>
                            系统信息
                        </h3>
                    </div>
                    <div class="system-info-grid">
                        <div class="info-row">
                            <span class="info-label">系统运行时间</span>
                            <span class="info-value">${this.formatUptime(data.uptime_seconds || 0)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">最后检查时间</span>
                            <span class="info-value">${UI.formatDateTime(data.last_check)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">系统版本</span>
                            <span class="info-value">v1.0.0</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Python 版本</span>
                            <span class="info-value">3.13+</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 获取服务状态摘要
     */
    getServicesSummary(services) {
        const healthy = services.filter(s => s.status === 'healthy').length;
        const total = services.length;
        const allHealthy = healthy === total;
        return `<span class="summary-badge ${allHealthy ? 'success' : 'warning'}">${healthy}/${total} 正常</span>`;
    },

    /**
     * 渲染单个服务项
     */
    renderServiceItem(service) {
        const statusClass = {
            'healthy': 'healthy',
            'unhealthy': 'unhealthy',
            'degraded': 'degraded'
        }[service.status] || 'unhealthy';

        const statusText = {
            'healthy': '健康',
            'unhealthy': '异常',
            'degraded': '降级'
        }[service.status] || '未知';

        return `
            <div class="service-item ${statusClass}">
                <div class="service-status-indicator">
                    <span class="status-dot ${statusClass}"></span>
                    <span class="status-pulse ${statusClass}"></span>
                </div>
                <div class="service-content">
                    <div class="service-name">${service.name}</div>
                    <div class="service-meta">
                        <span class="service-status-text">${statusText}</span>
                        ${service.latency_ms ? `<span class="service-latency">${service.latency_ms}ms</span>` : ''}
                    </div>
                    ${service.message ? `<div class="service-message">${this.escapeHtml(service.message)}</div>` : ''}
                </div>
            </div>
        `;
    },

    /**
     * 渲染 Tab 导航（已移除，直接显示日志）
     */
    renderTabs() {
        return '';
    },

    /**
     * 渲染 Tab 内容（直接显示日志）
     */
    renderTabContent() {
        return this.renderLogsTab();
    },

    /**
     * 渲染日志查询区域
     */
    renderLogsSection() {
        return `
            <div class="logs-card health-card">
                <div class="card-header-row">
                    <h3 class="card-title">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="16" y1="13" x2="8" y2="13"/>
                            <line x1="16" y1="17" x2="8" y2="17"/>
                        </svg>
                        日志查询
                    </h3>
                    <div class="card-actions">
                        <div class="export-dropdown">
                            <button class="btn btn-outline btn-sm" onclick="MonitorPage.toggleExportMenu()">
                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                    <polyline points="7 10 12 15 17 10"/>
                                    <line x1="12" y1="15" x2="12" y2="3"/>
                                </svg>
                                导出
                                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="6 9 12 15 18 9"/>
                                </svg>
                            </button>
                            <div class="export-menu" id="exportMenu">
                                <button class="export-menu-item" onclick="MonitorPage.exportLogs('json')">
                                    <span class="export-icon">JSON</span>
                                    <span class="export-label">JSON 格式</span>
                                </button>
                                <button class="export-menu-item" onclick="MonitorPage.exportLogs('csv')">
                                    <span class="export-icon">CSV</span>
                                    <span class="export-label">CSV 格式</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 筛选区域 -->
                <div class="logs-filter-section">
                    <div class="filter-row-compact">
                        <!-- 时间范围 -->
                        <div class="filter-item-compact">
                            <label class="filter-label-compact">时间范围</label>
                            <div class="time-range-select-wrapper">
                                <select class="form-select-compact" id="timeRangeSelect" onchange="MonitorPage.onTimeRangeChange(this.value)">
                                    <option value="5min" ${this.currentTimeRange === '5min' ? 'selected' : ''}>最近 5 分钟</option>
                                    <option value="30min" ${this.currentTimeRange === '30min' ? 'selected' : ''}>最近 30 分钟</option>
                                    <option value="3hours" ${this.currentTimeRange === '3hours' ? 'selected' : ''}>最近 3 小时</option>
                                    <option value="today" ${this.currentTimeRange === 'today' ? 'selected' : ''}>今天</option>
                                    <option value="yesterday" ${this.currentTimeRange === 'yesterday' ? 'selected' : ''}>昨天</option>
                                    <option value="7days" ${this.currentTimeRange === '7days' ? 'selected' : ''}>最近 7 天</option>
                                    <option value="30days" ${this.currentTimeRange === '30days' ? 'selected' : ''}>最近 30 天</option>
                                    <option value="custom" ${this.currentTimeRange === 'custom' ? 'selected' : ''}>自定义...</option>
                                </select>
                                <svg class="select-arrow" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="6 9 12 15 18 9"/>
                                </svg>
                            </div>
                        </div>
                        
                        <!-- 日志级别 -->
                        <div class="filter-item-compact">
                            <label class="filter-label-compact">日志级别</label>
                            <div class="level-dropdown-compact" id="levelDropdown">
                                <button class="level-dropdown-btn-compact" onclick="MonitorPage.toggleLevelDropdown(event)">
                                    <span class="selected-levels-badge">${this.renderSelectedLevelsBadge()}</span>
                                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="6 9 12 15 18 9"/>
                                    </svg>
                                </button>
                                <div class="level-dropdown-menu-compact" id="levelDropdownMenu">
                                    <div class="level-options-header">
                                        <span>选择日志级别</span>
                                        <button class="level-select-all" onclick="MonitorPage.toggleAllLevels(event)">
                                            ${this.selectedLevels.length === 6 ? '取消全选' : '全选'}
                                        </button>
                                    </div>
                                    <div class="level-options-grid">
                                        ${this.renderLevelOptionsCompact()}
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 关键词搜索 -->
                        <div class="filter-item-compact filter-item-keyword">
                            <label class="filter-label-compact">关键词</label>
                            <div class="keyword-input-wrapper">
                                <svg class="search-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="8"/>
                                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                                </svg>
                                <input type="text" class="form-input-compact" id="logKeyword" 
                                       placeholder="搜索关键词..." 
                                       value="${this.searchKeyword}"
                                       onkeypress="if(event.key==='Enter')MonitorPage.handleSearch()">
                                ${this.searchKeyword ? '<button class="clear-keyword-btn" onclick="MonitorPage.clearKeyword()">×</button>' : ''}
                            </div>
                        </div>
                        
                        <!-- 排序 -->
                        <div class="filter-item-compact">
                            <label class="filter-label-compact">排序</label>
                            <button class="sort-btn-compact ${this.logSortOrder}" onclick="MonitorPage.toggleSortOrder()" id="sortOrderBtn">
                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="12" y1="5" x2="12" y2="19"/>
                                    <polyline points="${this.logSortOrder === 'desc' ? '19 12 12 19 5 12' : '5 12 12 5 19 12'}"/>
                                </svg>
                                <span>${this.logSortOrder === 'desc' ? '最新优先' : '最早优先'}</span>
                            </button>
                        </div>
                        
                        <!-- 搜索按钮 -->
                        <div class="filter-item-compact filter-item-search">
                            <button class="btn btn-primary btn-search" id="searchLogsBtn" onclick="MonitorPage.handleSearch()">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="8"/>
                                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                                </svg>
                                搜索
                            </button>
                        </div>
                    </div>
                    
                    <!-- 自定义时间范围 -->
                    <div class="custom-time-range-compact" id="customTimeRange" style="display: ${this.currentTimeRange === 'custom' ? 'flex' : 'none'};">
                        <div class="custom-time-inputs-compact">
                            <div class="time-input-item">
                                <label>开始时间</label>
                                <input type="datetime-local" class="form-input-compact" id="customStartTime">
                            </div>
                            <span class="time-range-arrow">→</span>
                            <div class="time-input-item">
                                <label>结束时间</label>
                                <input type="datetime-local" class="form-input-compact" id="customEndTime">
                            </div>
                            <button class="btn btn-primary btn-sm" onclick="MonitorPage.applyCustomTimeRange()">应用</button>
                        </div>
                    </div>
                </div>
                
                <!-- 日志列表 -->
                <div class="logs-list-container" id="logsList">
                    <div class="logs-empty-state">
                        <div class="empty-icon">
                            <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" stroke-width="1">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14 2 14 8 20 8"/>
                                <line x1="16" y1="13" x2="8" y2="13" opacity="0.5"/>
                                <line x1="16" y1="17" x2="8" y2="17" opacity="0.5"/>
                            </svg>
                        </div>
                        <div class="empty-text">
                            <h4>暂无日志数据</h4>
                            <p>请设置筛选条件后点击搜索按钮</p>
                        </div>
                    </div>
                </div>
                
                <!-- 分页 -->
                <div class="logs-pagination-compact" id="logsPagination"></div>
            </div>
        `;
    },

    /**
     * 时间范围选择变化处理
     */
    onTimeRangeChange(value) {
        this.currentTimeRange = value;
        const customRange = document.getElementById('customTimeRange');
        if (customRange) {
            customRange.style.display = value === 'custom' ? 'flex' : 'none';
        }
        if (value !== 'custom') {
            this.handleSearch();
        }
    },

    /**
     * 渲染选中级别的徽章
     */
    renderSelectedLevelsBadge() {
        if (this.selectedLevels.length === 0) {
            return '<span class="no-selection">未选择</span>';
        }
        if (this.selectedLevels.length === 6) {
            return '<span class="all-selected">全部级别</span>';
        }
        // 显示选中的级别徽章
        return this.selectedLevels.map(level => {
            const colors = {
                'DEBUG': '#6b7280',
                'INFO': '#3b82f6',
                'SUCCESS': '#22c55e',
                'WARNING': '#f59e0b',
                'ERROR': '#ef4444',
                'CRITICAL': '#dc2626'
            };
            return `<span class="level-mini-badge" style="background:${colors[level]}">${level.charAt(0)}</span>`;
        }).join('');
    },

    /**
     * 渲染紧凑的级别选项
     */
    renderLevelOptionsCompact() {
        const levels = [
            { value: 'DEBUG', label: 'DEBUG', color: '#6b7280', desc: '调试信息' },
            { value: 'INFO', label: 'INFO', color: '#3b82f6', desc: '常规信息' },
            { value: 'SUCCESS', label: 'SUCCESS', color: '#22c55e', desc: '成功信息' },
            { value: 'WARNING', label: 'WARNING', color: '#f59e0b', desc: '警告信息' },
            { value: 'ERROR', label: 'ERROR', color: '#ef4444', desc: '错误信息' },
            { value: 'CRITICAL', label: 'CRITICAL', color: '#dc2626', desc: '严重错误' }
        ];

        return levels.map(level => `
            <label class="level-option-compact ${this.selectedLevels.includes(level.value) ? 'selected' : ''}">
                <input type="checkbox" value="${level.value}"
                       ${this.selectedLevels.includes(level.value) ? 'checked' : ''}
                       onchange="MonitorPage.toggleLevelCompact('${level.value}')">
                <span class="level-badge-compact" style="background: ${level.color}">${level.label}</span>
                <span class="level-desc">${level.desc}</span>
            </label>
        `).join('');
    },

    /**
     * 切换日志级别（紧凑版）
     */
    toggleLevelCompact(level) {
        this.toggleLevel(level);
        // 更新按钮显示
        const btn = document.querySelector('.selected-levels-badge');
        if (btn) {
            btn.innerHTML = this.renderSelectedLevelsBadge();
        }
        // 更新选项样式
        document.querySelectorAll('.level-option-compact').forEach(opt => {
            const checkbox = opt.querySelector('input');
            if (checkbox) {
                opt.classList.toggle('selected', checkbox.checked);
            }
        });
        // 更新全选按钮文本
        const selectAllBtn = document.querySelector('.level-select-all');
        if (selectAllBtn) {
            selectAllBtn.textContent = this.selectedLevels.length === 6 ? '取消全选' : '全选';
        }
    },

    /**
     * 切换全选/取消全选
     */
    toggleAllLevels(event) {
        event.stopPropagation();
        if (this.selectedLevels.length === 6) {
            this.selectedLevels = [];
        } else {
            this.selectedLevels = ['DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL'];
        }
        // 更新复选框状态
        document.querySelectorAll('.level-option-compact input').forEach(checkbox => {
            checkbox.checked = this.selectedLevels.includes(checkbox.value);
            checkbox.closest('.level-option-compact').classList.toggle('selected', checkbox.checked);
        });
        // 更新按钮显示
        const btn = document.querySelector('.selected-levels-badge');
        if (btn) {
            btn.innerHTML = this.renderSelectedLevelsBadge();
        }
        // 更新全选按钮文本
        const selectAllBtn = document.querySelector('.level-select-all');
        if (selectAllBtn) {
            selectAllBtn.textContent = this.selectedLevels.length === 6 ? '取消全选' : '全选';
        }
    },

    /**
     * 清除关键词
     */
    clearKeyword() {
        this.searchKeyword = '';
        const input = document.getElementById('logKeyword');
        if (input) {
            input.value = '';
            // 移除清除按钮
            const clearBtn = input.parentElement.querySelector('.clear-keyword-btn');
            if (clearBtn) clearBtn.remove();
        }
    },

    /**
     * 渲染日志查看 Tab
     */
    renderLogsTab() {
        return `
            <div class="logs-tab">
                <!-- 时间范围快捷选择 -->
                <div class="time-range-section">
                    <div class="time-range-label">时间范围</div>
                    <div class="time-range-buttons">
                        ${this.renderTimeRangeButtons()}
                    </div>
                    <div class="custom-time-range" id="customTimeRange" style="display: none;">
                        <div class="custom-time-inputs">
                            <div class="time-input-group">
                                <label>开始时间</label>
                                <input type="datetime-local" class="form-control" id="customStartTime">
                            </div>
                            <div class="time-input-group">
                                <label>结束时间</label>
                                <input type="datetime-local" class="form-control" id="customEndTime">
                            </div>
                            <button class="btn btn-primary btn-sm" onclick="MonitorPage.applyCustomTimeRange()">应用</button>
                        </div>
                    </div>
                </div>

                <!-- 筛选区域 -->
                <div class="filter-card">
                    <div class="filter-row">
                        <!-- 日志级别多选 -->
                        <div class="filter-item level-filter">
                            <label class="filter-label">日志级别</label>
                            <div class="level-dropdown" id="levelDropdown">
                                <button class="level-dropdown-btn" onclick="MonitorPage.toggleLevelDropdown()">
                                    <span class="selected-levels-text">${this.getSelectedLevelsText()}</span>
                                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="6 9 12 15 18 9"/>
                                    </svg>
                                </button>
                                <div class="level-dropdown-menu" id="levelDropdownMenu">
                                    ${this.renderLevelOptions()}
                                </div>
                            </div>
                        </div>

                        <!-- 关键词搜索 -->
                        <div class="filter-item keyword-filter">
                            <label class="filter-label">关键词搜索</label>
                            <div class="keyword-input-group">
                                <input type="text" class="form-control" id="logKeyword" placeholder="输入关键词..." value="${this.searchKeyword}">
                                <button class="btn btn-primary" onclick="MonitorPage.handleSearch()">
                                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="11" cy="11" r="8"/>
                                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                                    </svg>
                                    搜索
                                </button>
                            </div>
                        </div>

                        <!-- 排序按钮 -->
                        <div class="filter-item sort-filter">
                            <label class="filter-label">时间排序</label>
                            <button class="btn btn-outline sort-btn ${this.logSortOrder}" onclick="MonitorPage.toggleSortOrder()" id="sortBtn">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="12" y1="5" x2="12" y2="19"/>
                                    <polyline points="${this.logSortOrder === 'desc' ? '19 12 12 19 5 12' : '5 12 12 5 19 12'}"/>
                                </svg>
                                ${this.logSortOrder === 'desc' ? '最新在前' : '最早在前'}
                            </button>
                        </div>

                        <!-- 导出按钮 -->
                        <div class="filter-item export-filter">
                            <label class="filter-label">导出</label>
                            <div class="export-buttons">
                                <button class="btn btn-outline" onclick="MonitorPage.exportLogs('json')">
                                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                        <polyline points="7 10 12 15 17 10"/>
                                        <line x1="12" y1="15" x2="12" y2="3"/>
                                    </svg>
                                    JSON
                                </button>
                                <button class="btn btn-outline" onclick="MonitorPage.exportLogs('csv')">
                                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                    </svg>
                                    CSV
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 日志列表 -->
                <div class="logs-list" id="logsList">
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        <p>点击搜索按钮加载日志</p>
                    </div>
                </div>

                <!-- 分页 -->
                <div class="logs-pagination" id="logsPagination"></div>
            </div>
        `;
    },

    /**
     * 渲染时间范围快捷按钮
     */
    renderTimeRangeButtons() {
        const ranges = [
            { id: '5min', label: '最近5分钟' },
            { id: '30min', label: '最近30分钟' },
            { id: '3hours', label: '最近3小时' },
            { id: 'today', label: '今天' },
            { id: 'yesterday', label: '昨天' },
            { id: '7days', label: '最近7天' },
            { id: '30days', label: '最近30天' },
            { id: 'custom', label: '自定义' }
        ];

        return ranges.map(range => `
            <button class="time-range-btn ${this.currentTimeRange === range.id ? 'active' : ''}"
                    data-range="${range.id}"
                    onclick="MonitorPage.selectTimeRange('${range.id}')">
                ${range.label}
            </button>
        `).join('');
    },

    /**
     * 渲染日志级别选项
     */
    renderLevelOptions() {
        const levels = [
            { value: 'DEBUG', label: 'DEBUG', color: '#6b7280' },
            { value: 'INFO', label: 'INFO', color: '#3b82f6' },
            { value: 'SUCCESS', label: 'SUCCESS', color: '#22c55e' },
            { value: 'WARNING', label: 'WARNING', color: '#f59e0b' },
            { value: 'ERROR', label: 'ERROR', color: '#ef4444' },
            { value: 'CRITICAL', label: 'CRITICAL', color: '#dc2626' }
        ];

        return levels.map(level => `
            <label class="level-option">
                <input type="checkbox" value="${level.value}"
                       ${this.selectedLevels.includes(level.value) ? 'checked' : ''}
                       onchange="MonitorPage.toggleLevel('${level.value}')">
                <span class="level-badge" style="background: ${level.color}">${level.label}</span>
            </label>
        `).join('');
    },

    /**
     * 获取选中级别的显示文本
     */
    getSelectedLevelsText() {
        if (this.selectedLevels.length === 0) {
            return '请选择级别';
        }
        if (this.selectedLevels.length === 6) {
            return '全部级别';
        }
        return this.selectedLevels.join(', ');
    },

    /**
     * 选择时间范围
     */
    selectTimeRange(rangeId) {
        this.currentTimeRange = rangeId;

        // 更新按钮状态
        document.querySelectorAll('.time-range-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.range === rangeId);
        });

        // 显示/隐藏自定义时间范围
        const customRange = document.getElementById('customTimeRange');
        if (customRange) {
            customRange.style.display = rangeId === 'custom' ? 'block' : 'none';
        }

        // 非自定义时自动搜索
        if (rangeId !== 'custom') {
            this.handleSearch();
        }
    },

    /**
     * 应用自定义时间范围
     */
    applyCustomTimeRange() {
        const startTime = document.getElementById('customStartTime')?.value;
        const endTime = document.getElementById('customEndTime')?.value;

        if (!startTime || !endTime) {
            UI.toast('请选择开始和结束时间', 'warning');
            return;
        }

        this.customTimeRange.start = startTime;
        this.customTimeRange.end = endTime;
        this.handleSearch();
    },

    /**
     * 获取时间范围参数
     */
    getTimeRangeParams() {
        const now = new Date();
        let startTime, endTime;

        switch (this.currentTimeRange) {
            case '5min':
                startTime = new Date(now.getTime() - 5 * 60 * 1000);
                endTime = now;
                break;
            case '30min':
                startTime = new Date(now.getTime() - 30 * 60 * 1000);
                endTime = now;
                break;
            case '3hours':
                startTime = new Date(now.getTime() - 3 * 60 * 60 * 1000);
                endTime = now;
                break;
            case 'today':
                startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
                endTime = now;
                break;
            case 'yesterday':
                startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 0, 0, 0);
                endTime = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 23, 59, 59);
                break;
            case '7days':
                startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                endTime = now;
                break;
            case '30days':
                startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                endTime = now;
                break;
            case 'custom':
                startTime = this.customTimeRange.start ? new Date(this.customTimeRange.start) : null;
                endTime = this.customTimeRange.end ? new Date(this.customTimeRange.end) : null;
                break;
            default:
                startTime = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
                endTime = now;
        }

        return {
            start_time: startTime ? this.formatLocalDateTime(startTime) : null,
            end_time: endTime ? this.formatLocalDateTime(endTime) : null
        };
    },

    /**
     * 格式化为本地时间字符串（不带时区）
     */
    formatLocalDateTime(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
    },

    /**
     * 切换日志级别下拉框
     */
    toggleLevelDropdown(event) {
        if (event) {
            event.stopPropagation();
        }
        const menu = document.getElementById('levelDropdownMenu');
        if (menu) {
            menu.classList.toggle('show');
        }
    },

    /**
     * 切换导出下拉菜单
     */
    toggleExportMenu() {
        const menu = document.getElementById('exportMenu');
        if (menu) {
            menu.classList.toggle('show');
        }
    },

    /**
     * 切换日志级别选择
     */
    toggleLevel(level) {
        const index = this.selectedLevels.indexOf(level);
        if (index > -1) {
            this.selectedLevels.splice(index, 1);
        } else {
            this.selectedLevels.push(level);
        }

        // 更新显示文本
        const textEl = document.querySelector('.selected-levels-text');
        if (textEl) {
            textEl.textContent = this.getSelectedLevelsText();
        }
    },

    /**
     * 切换排序顺序
     */
    toggleSortOrder() {
        this.logSortOrder = this.logSortOrder === 'desc' ? 'asc' : 'desc';

        // 更新按钮状态
        const btn = document.getElementById('sortOrderBtn');
        if (btn) {
            btn.className = `sort-btn-compact ${this.logSortOrder}`;
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <polyline points="${this.logSortOrder === 'desc' ? '19 12 12 19 5 12' : '5 12 12 5 19 12'}"/>
                </svg>
                <span>${this.logSortOrder === 'desc' ? '最新优先' : '最早优先'}</span>
            `;
        }

        // 重新加载日志
        if (this.logsData) {
            this.handleSearch();
        }
    },

    /**
     * 处理搜索
     */
    async handleSearch() {
        this.currentLogPage = 1;
        await this.loadLogs(1);
    },

    /**
     * 处理手动刷新健康检查
     */
    async handleRefreshHealth() {
        if (this.isRefreshing) return;

        const btn = document.getElementById('refreshHealthBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `
                <svg class="spinning" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
                检查中...
            `;
        }

        this.isRefreshing = true;
        await this.loadHealthData();
        this.isRefreshing = false;

        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="23 4 23 10 17 10"/>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
                立即检查
            `;
        }

        UI.toast('系统状态已更新', 'success');
    },

    /**
     * 初始化页面事件
     */
    initEvents() {
        this.initLogEvents();

        // 点击其他地方关闭下拉框
        document.addEventListener('click', (e) => {
            // 关闭级别下拉框
            const levelDropdown = document.getElementById('levelDropdown');
            const levelMenu = document.getElementById('levelDropdownMenu');
            if (levelDropdown && levelMenu && !levelDropdown.contains(e.target)) {
                levelMenu.classList.remove('show');
            }

            // 关闭导出下拉菜单
            const exportMenu = document.getElementById('exportMenu');
            const exportBtn = document.querySelector('.export-dropdown');
            if (exportMenu && exportBtn && !exportBtn.contains(e.target)) {
                exportMenu.classList.remove('show');
            }
        });
    },

    /**
     * 初始化日志相关事件
     */
    initLogEvents() {
        // 关键词输入回车搜索
        const keywordInput = document.getElementById('logKeyword');
        if (keywordInput) {
            keywordInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSearch();
                }
            });
        }
    },

    /**
     * 加载日志数据
     */
    async loadLogs(page = 1) {
        const keyword = document.getElementById('logKeyword')?.value || '';
        this.searchKeyword = keyword;

        const timeRange = this.getTimeRangeParams();

        const logsList = document.getElementById('logsList');
        if (logsList) {
            logsList.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <span>加载中...</span>
                </div>
            `;
        }

        try {
            const params = {
                page,
                page_size: 50,
                order: this.logSortOrder
            };

            if (timeRange.start_time) params.start_time = timeRange.start_time;
            if (timeRange.end_time) params.end_time = timeRange.end_time;
            if (this.selectedLevels.length > 0 && this.selectedLevels.length < 6) {
                params.level = this.selectedLevels;
            }
            if (keyword) params.keyword = keyword;

            const response = await monitorApi.getLogs(params);
            this.logsData = response.data;

            this.renderLogsList();
            this.renderLogsPagination();
        } catch (error) {
            console.error('加载日志失败:', error);
            if (logsList) {
                logsList.innerHTML = UI.renderError('加载日志失败');
            }
        }
    },

    /**
     * 渲染日志列表
     */
    renderLogsList() {
        const logsList = document.getElementById('logsList');
        if (!logsList || !this.logsData) return;

        const logs = this.logsData.items || [];

        if (logs.length === 0) {
            logsList.innerHTML = `
                <div class="logs-empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" stroke-width="1">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="16" y1="13" x2="8" y2="13" opacity="0.5"/>
                            <line x1="16" y1="17" x2="8" y2="17" opacity="0.5"/>
                        </svg>
                    </div>
                    <div class="empty-text">
                        <h4>未找到匹配的日志</h4>
                        <p>请尝试调整筛选条件</p>
                    </div>
                </div>
            `;
            return;
        }

        logsList.innerHTML = `
            <div class="logs-table-container">
                <table class="logs-table-new">
                    <thead>
                        <tr>
                            <th class="col-time">时间</th>
                            <th class="col-level">级别</th>
                            <th class="col-module">模块</th>
                            <th class="col-function">函数</th>
                            <th class="col-line">行号</th>
                            <th class="col-message">消息内容</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map(log => this.renderLogEntry(log)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * 渲染单条日志
     */
    renderLogEntry(log) {
        const levelClass = this.getLevelClass(log.level);
        const isExpanded = this.expandedLogs.has(log.id);
        const hasDetails = log.extra || log.exception;

        return `
            <tr class="log-row ${levelClass}" data-log-id="${log.id}">
                <td class="log-cell log-time-cell">
                    <span class="log-time-text">${UI.formatDateTime(log.timestamp)}</span>
                </td>
                <td class="log-cell log-level-cell">
                    <span class="log-level-tag ${levelClass}">${log.level}</span>
                </td>
                <td class="log-cell log-module-cell">${log.module || '-'}</td>
                <td class="log-cell log-function-cell">${log.function || '-'}</td>
                <td class="log-cell log-line-cell">${log.line || '-'}</td>
                <td class="log-cell log-message-cell" onclick="MonitorPage.toggleLogDetail('${log.id}')">
                    <div class="log-message-wrapper">
                        <span class="log-message-text">${this.escapeHtml(log.message)}</span>
                        ${hasDetails ? `
                            <span class="log-expand-btn ${isExpanded ? 'expanded' : ''}">
                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="6 9 12 15 18 9"/>
                                </svg>
                            </span>
                        ` : ''}
                    </div>
                    ${isExpanded && hasDetails ? this.renderLogDetailInline(log) : ''}
                </td>
            </tr>
        `;
    },

    /**
     * 渲染日志详情（内联版本）
     */
    renderLogDetailInline(log) {
        let detailHtml = '<div class="log-detail-inline">';
        
        if (log.extra && Object.keys(log.extra).length > 0) {
            detailHtml += `
                <div class="detail-block extra-block">
                    <div class="detail-label">额外信息</div>
                    <pre class="detail-content">${this.escapeHtml(JSON.stringify(log.extra, null, 2))}</pre>
                </div>
            `;
        }

        if (log.exception) {
            detailHtml += `
                <div class="detail-block exception-block">
                    <div class="detail-label">异常信息</div>
                    <pre class="detail-content">${this.escapeHtml(typeof log.exception === 'string' ? log.exception : JSON.stringify(log.exception, null, 2))}</pre>
                </div>
            `;
        }

        detailHtml += '</div>';
        return detailHtml;
    },

    /**
     * 渲染日志详情
     */
    renderLogDetail(log) {
        let detailHtml = '<div class="log-detail">';

        if (log.extra && Object.keys(log.extra).length > 0) {
            detailHtml += `
                <div class="log-detail-section">
                    <div class="log-detail-title">额外信息 (Extra)</div>
                    <pre class="log-detail-content">${this.escapeHtml(JSON.stringify(log.extra, null, 2))}</pre>
                </div>
            `;
        }

        if (log.exception) {
            detailHtml += `
                <div class="log-detail-section exception">
                    <div class="log-detail-title">异常信息 (Exception)</div>
                    <pre class="log-detail-content">${this.escapeHtml(typeof log.exception === 'string' ? log.exception : JSON.stringify(log.exception, null, 2))}</pre>
                </div>
            `;
        }

        detailHtml += '</div>';
        return detailHtml;
    },

    /**
     * 切换日志详情展开/收起
     */
    toggleLogDetail(logId) {
        const logRow = document.querySelector(`.log-row[data-log-id="${logId}"]`);
        if (!logRow) return;

        const messageCell = logRow.querySelector('.log-message-cell');
        if (!messageCell) return;

        if (this.expandedLogs.has(logId)) {
            this.expandedLogs.delete(logId);
            // 移除详情
            const detail = messageCell.querySelector('.log-detail-inline');
            if (detail) detail.remove();
            // 更新图标
            const btn = messageCell.querySelector('.log-expand-btn');
            if (btn) btn.classList.remove('expanded');
        } else {
            this.expandedLogs.add(logId);
            // 找到对应的日志数据
            const log = this.logsData?.items?.find(l => l.id === logId);
            if (log) {
                // 插入详情
                const wrapper = messageCell.querySelector('.log-message-wrapper');
                if (wrapper) {
                    wrapper.insertAdjacentHTML('afterend', this.renderLogDetailInline(log));
                }
                // 更新图标
                const btn = messageCell.querySelector('.log-expand-btn');
                if (btn) btn.classList.add('expanded');
            }
        }
    },

    /**
     * 获取日志级别样式类
     */
    getLevelClass(level) {
        const levelMap = {
            'DEBUG': 'level-debug',
            'INFO': 'level-info',
            'SUCCESS': 'level-success',
            'WARNING': 'level-warning',
            'ERROR': 'level-error',
            'CRITICAL': 'level-critical'
        };
        return levelMap[level] || 'level-info';
    },

    /**
     * 渲染日志分页
     */
    renderLogsPagination() {
        const pagination = document.getElementById('logsPagination');
        if (!pagination || !this.logsData) return;

        const { page, total_pages, total } = this.logsData;
        
        // 生成分页按钮
        let paginationHtml = '';
        
        // 上一页
        paginationHtml += `
            <button class="pagination-btn ${page <= 1 ? 'disabled' : ''}" 
                    onclick="MonitorPage.loadLogs(${page - 1})" 
                    ${page <= 1 ? 'disabled' : ''}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 18 9 12 15 6"/>
                </svg>
            </button>
        `;
        
        // 页码
        const maxVisiblePages = 5;
        let startPage = Math.max(1, page - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(total_pages, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        if (startPage > 1) {
            paginationHtml += `<button class="pagination-btn" onclick="MonitorPage.loadLogs(1)">1</button>`;
            if (startPage > 2) {
                paginationHtml += `<span class="pagination-ellipsis">...</span>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <button class="pagination-btn ${i === page ? 'active' : ''}" 
                        onclick="MonitorPage.loadLogs(${i})">
                    ${i}
                </button>
            `;
        }
        
        if (endPage < total_pages) {
            if (endPage < total_pages - 1) {
                paginationHtml += `<span class="pagination-ellipsis">...</span>`;
            }
            paginationHtml += `<button class="pagination-btn" onclick="MonitorPage.loadLogs(${total_pages})">${total_pages}</button>`;
        }
        
        // 下一页
        paginationHtml += `
            <button class="pagination-btn ${page >= total_pages ? 'disabled' : ''}" 
                    onclick="MonitorPage.loadLogs(${page + 1})" 
                    ${page >= total_pages ? 'disabled' : ''}>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                </svg>
            </button>
        `;

        pagination.innerHTML = `
            <div class="pagination-info">
                <span class="pagination-total">共 <strong>${total}</strong> 条记录</span>
                <span class="pagination-current">第 ${page}/${total_pages} 页</span>
            </div>
            <div class="pagination-controls">
                ${paginationHtml}
            </div>
        `;
    },

    /**
     * 导出日志
     */
    async exportLogs(format) {
        const keyword = document.getElementById('logKeyword')?.value || '';
        const timeRange = this.getTimeRangeParams();

        try {
            const params = { format };

            if (timeRange.start_time) params.start_time = timeRange.start_time;
            if (timeRange.end_time) params.end_time = timeRange.end_time;
            if (this.selectedLevels.length > 0 && this.selectedLevels.length < 6) {
                params.level = this.selectedLevels;
            }
            if (keyword) params.keyword = keyword;

            await monitorApi.exportLogs(params);
            UI.toast('日志导出已开始', 'success');
        } catch (error) {
            console.error('导出日志失败:', error);
            UI.toast('导出日志失败', 'error');
        }
    },

    /**
     * 初始化 ECharts 图表
     */
    initCharts() {
        if (typeof echarts === 'undefined') return;

        const resources = this.healthData?.resources || {};

        // 汽车仪表盘风格配置
        const createGaugeOption = (value, colors, unit = '%') => ({
            series: [{
                type: 'gauge',
                startAngle: 200,
                endAngle: -20,
                min: 0,
                max: 100,
                splitNumber: 10,
                itemStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 1, y2: 0,
                        colorStops: [
                            { offset: 0, color: colors[0] },
                            { offset: 1, color: colors[1] }
                        ]
                    }
                },
                progress: {
                    show: true,
                    width: 20,
                    roundCap: true
                },
                pointer: {
                    show: true,
                    length: '60%',
                    width: 6,
                    itemStyle: {
                        color: colors[0]
                    }
                },
                axisLine: {
                    lineStyle: {
                        width: 20,
                        color: [[1, '#e5e7eb']]
                    }
                },
                axisTick: {
                    show: true,
                    distance: -28,
                    length: 6,
                    lineStyle: {
                        color: '#999',
                        width: 1
                    }
                },
                splitLine: {
                    show: true,
                    distance: -32,
                    length: 12,
                    lineStyle: {
                        color: '#666',
                        width: 2
                    }
                },
                axisLabel: {
                    show: true,
                    distance: -50,
                    fontSize: 10,
                    color: '#666',
                    formatter: (val) => {
                        if (val === 0 || val === 50 || val === 100) return val;
                        return '';
                    }
                },
                detail: {
                    show: true,
                    valueAnimation: true,
                    fontSize: 36,
                    fontWeight: 'bold',
                    color: colors[0],
                    offsetCenter: [0, '70%'],
                    formatter: `{value}${unit}`
                },
                data: [{ value: Math.round(value || 0) }]
            }]
        });

        // CPU 仪表盘
        const cpuGauge = document.getElementById('cpuGauge');
        if (cpuGauge) {
            this.charts.cpu = echarts.init(cpuGauge);
            this.charts.cpu.setOption(createGaugeOption(
                resources.cpu_percent || 0,
                ['#3370ff', '#6690ff']
            ));
        }

        // 内存仪表盘
        const memoryGauge = document.getElementById('memoryGauge');
        if (memoryGauge) {
            this.charts.memory = echarts.init(memoryGauge);
            this.charts.memory.setOption(createGaugeOption(
                resources.memory_percent || 0,
                ['#22c55e', '#4ade80']
            ));
        }

        // 磁盘仪表盘
        const diskGauge = document.getElementById('diskGauge');
        if (diskGauge) {
            this.charts.disk = echarts.init(diskGauge);
            this.charts.disk.setOption(createGaugeOption(
                resources.disk_percent || 0,
                ['#f59e0b', '#fbbf24']
            ));
        }
    },

    /**
     * 清除缓存
     */
    clearCache() {
        this.healthData = null;
        this.logsData = null;
        this.expandedLogs.clear();
    },

    /**
     * 格式化运行时间
     */
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        let result = '';
        if (days > 0) result += `${days} 天 `;
        if (hours > 0) result += `${hours} 小时 `;
        result += `${minutes} 分钟`;
        return result;
    },

    /**
     * HTML 转义
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

/**
 * 监控 API 接口
 */
const monitorApi = {
    /**
     * 获取日志列表
     */
    getLogs(params) {
        return api.get('/monitor/logs', params);
    },

    /**
     * 导出日志
     */
    exportLogs(params) {
        const query = new URLSearchParams();
        if (params.start_time) query.append('start_time', params.start_time);
        if (params.end_time) query.append('end_time', params.end_time);
        if (params.level) {
            params.level.forEach(l => query.append('level', l));
        }
        if (params.keyword) query.append('keyword', params.keyword);
        query.append('format', params.format);

        window.open(`${API_BASE_URL}/monitor/logs/export?${query.toString()}`, '_blank');
        return Promise.resolve();
    },

    /**
     * 获取健康检查
     */
    getHealth() {
        return api.get('/monitor/health');
    },

    /**
     * 获取指标
     */
    getMetrics() {
        return api.get('/monitor/metrics');
    },

    /**
     * 获取指标历史
     */
    getMetricsHistory(duration = 3600) {
        return api.get('/monitor/metrics/history', { duration });
    }
};

// 注入页面样式
if (!document.getElementById('monitor-styles')) {
    const monitorStyles = document.createElement('style');
    monitorStyles.id = 'monitor-styles';
    monitorStyles.textContent = `
    /* ========== 页面布局 ========== */
    .monitor-page {
        display: flex;
        flex-direction: column;
        gap: 24px;
    }

    .monitor-header {
        margin-bottom: 8px;
    }

    .page-title {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 8px 0;
    }

    .page-subtitle {
        font-size: 14px;
        color: var(--text-secondary);
        margin: 0;
    }

    /* ========== 健康检查区域 ========== */
    .health-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .health-card {
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
        padding: 20px;
        transition: box-shadow 0.2s ease;
    }

    .health-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    .resource-card {
        grid-column: 1 / -1;
    }

    .card-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }

    .card-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .card-title svg {
        color: var(--primary-color);
    }

    /* ========== 资源仪表盘 ========== */
    .resource-gauges {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
    }

    .gauge-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
        transition: transform 0.2s ease;
    }

    .gauge-item:hover {
        transform: translateY(-2px);
    }

    .gauge-chart {
        width: 220px;
        height: 160px;
    }

    .gauge-info {
        text-align: center;
        margin-top: 8px;
    }

    .gauge-label {
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 4px;
    }

    .gauge-detail {
        font-size: 13px;
        color: var(--text-muted);
        margin-top: 4px;
    }

    /* ========== 服务状态 ========== */
    .services-card {
        grid-column: 1 / 2;
    }

    .services-summary {
        font-size: 13px;
    }

    .summary-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 500;
    }

    .summary-badge.success {
        background: var(--success-bg);
        color: var(--success-color);
    }

    .summary-badge.warning {
        background: var(--warning-bg);
        color: var(--warning-color);
    }

    .services-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    .service-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
        border-left: 3px solid transparent;
        transition: all 0.2s ease;
    }

    .service-item.healthy {
        border-left-color: var(--success-color);
    }

    .service-item.unhealthy {
        border-left-color: var(--danger-color);
    }

    .service-item.degraded {
        border-left-color: var(--warning-color);
    }

    .service-status-indicator {
        position: relative;
        width: 12px;
        height: 12px;
        margin-top: 4px;
    }

    .monitor-page .status-dot {
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }

    .monitor-page .status-dot.healthy { background: var(--success-color); }
    .monitor-page .status-dot.unhealthy { background: var(--danger-color); }
    .monitor-page .status-dot.degraded { background: var(--warning-color); }

    .monitor-page .status-pulse {
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        animation: pulse-ring 1.5s ease-out infinite;
    }

    .status-pulse.healthy { background: var(--success-color); }
    .status-pulse.unhealthy { background: var(--danger-color); }
    .status-pulse.degraded { background: var(--warning-color); }

    @keyframes pulse-ring {
        0% { transform: scale(1); opacity: 0.8; }
        100% { transform: scale(2); opacity: 0; }
    }

    .service-content {
        flex: 1;
        min-width: 0;
    }

    .service-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 14px;
    }

    .service-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 4px;
    }

    .service-status-text {
        font-size: 12px;
        color: var(--text-secondary);
    }

    .service-latency {
        font-size: 11px;
        color: var(--text-muted);
        padding: 2px 6px;
        background: var(--bg-tertiary);
        border-radius: 4px;
    }

    .service-message {
        font-size: 11px;
        color: var(--danger-color);
        margin-top: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* ========== 系统信息 ========== */
    .system-card {
        grid-column: 2 / 3;
    }

    .system-info-grid {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .info-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-color);
    }

    .info-row:last-child {
        border-bottom: none;
    }

    .info-label {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .info-value {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary);
    }

    /* ========== 加载与错误状态 ========== */
    .health-loading,
    .health-error {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
        gap: 16px;
    }

    .health-loading {
        color: var(--text-muted);
    }

    .health-error {
        color: var(--danger-color);
    }

    .health-error svg {
        opacity: 0.5;
    }

    .error-text {
        font-size: 14px;
    }

    .loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid var(--border-color);
        border-top-color: var(--primary-color);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .spinning {
        animation: spin 0.8s linear infinite;
    }

    /* ========== Tab 导航 ========== */
    .tabs-container {
        display: flex;
        gap: 4px;
        background: var(--bg-secondary);
        padding: 4px;
        border-radius: var(--radius-lg);
    }

    .tab-btn {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px;
        background: transparent;
        border: none;
        border-radius: var(--radius-md);
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .tab-btn:hover {
        color: var(--text-primary);
        background: var(--bg-tertiary);
    }

    .tab-btn.active {
        background: var(--bg-primary);
        color: var(--primary-color);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    /* ========== Tab 内容 ========== */
    .tab-content {
        min-height: 400px;
    }

    /* ========== 时间范围选择 ========== */
    .time-range-section {
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
        padding: 16px 20px;
        margin-bottom: 16px;
    }

    .time-range-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 12px;
    }

    .time-range-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .time-range-btn {
        padding: 8px 16px;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 13px;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .time-range-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .time-range-btn.active {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
    }

    .custom-time-range {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-color);
    }

    .custom-time-inputs {
        display: flex;
        align-items: flex-end;
        gap: 12px;
        flex-wrap: wrap;
    }

    .time-input-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .time-input-group label {
        font-size: 12px;
        color: var(--text-secondary);
    }

    /* ========== 日志筛选区域（紧凑版） ========== */
    .logs-filter-section {
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
        padding: 16px;
        margin-bottom: 16px;
    }

    .filter-row-compact {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        align-items: flex-end;
    }

    .filter-item-compact {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .filter-label-compact {
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary);
    }

    /* 时间范围下拉选择 */
    .time-range-select-wrapper {
        position: relative;
    }

    .form-select-compact {
        appearance: none;
        padding: 8px 32px 8px 12px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 13px;
        color: var(--text-primary);
        cursor: pointer;
        min-width: 140px;
        transition: all 0.2s ease;
    }

    .form-select-compact:hover {
        border-color: var(--primary-color);
    }

    .form-select-compact:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    .select-arrow {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        pointer-events: none;
        color: var(--text-muted);
    }

    /* 日志级别下拉框（紧凑版） */
    .level-dropdown-compact {
        position: relative;
    }

    .level-dropdown-btn-compact {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        padding: 8px 12px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 13px;
        color: var(--text-primary);
        cursor: pointer;
        min-width: 140px;
        transition: all 0.2s ease;
    }

    .level-dropdown-btn-compact:hover {
        border-color: var(--primary-color);
    }

    .selected-levels-badge {
        display: flex;
        align-items: center;
        gap: 4px;
        flex-wrap: wrap;
    }

    .selected-levels-badge .no-selection {
        color: var(--text-muted);
    }

    .selected-levels-badge .all-selected {
        color: var(--text-primary);
        font-weight: 500;
    }

    .level-mini-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        color: white;
    }

    .level-dropdown-menu-compact {
        position: absolute;
        top: 100%;
        left: 0;
        margin-top: 4px;
        padding: 12px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        z-index: 100;
        display: none;
        min-width: 280px;
    }

    .level-dropdown-menu-compact.show {
        display: block;
    }

    .level-options-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }

    .level-options-header span {
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary);
    }

    .level-select-all {
        font-size: 12px;
        color: var(--primary-color);
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: background 0.2s ease;
    }

    .level-select-all:hover {
        background: var(--primary-bg);
    }

    .level-options-grid {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .level-option-compact {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        cursor: pointer;
        border-radius: var(--radius-sm);
        transition: background 0.2s ease;
    }

    .level-option-compact:hover {
        background: var(--bg-secondary);
    }

    .level-option-compact.selected {
        background: var(--primary-bg);
    }

    .level-option-compact input {
        width: 16px;
        height: 16px;
        cursor: pointer;
        accent-color: var(--primary-color);
    }

    .level-badge-compact {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        color: white;
        min-width: 70px;
        text-align: center;
    }

    .level-desc {
        font-size: 12px;
        color: var(--text-muted);
    }

    /* 关键词输入框 */
    .filter-item-keyword {
        flex: 1;
        min-width: 200px;
    }

    .keyword-input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
    }

    .keyword-input-wrapper .search-icon {
        position: absolute;
        left: 10px;
        color: var(--text-muted);
        pointer-events: none;
    }

    .form-input-compact {
        width: 100%;
        padding: 8px 12px;
        padding-left: 34px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 13px;
        color: var(--text-primary);
        transition: all 0.2s ease;
    }

    .form-input-compact:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    .form-input-compact::placeholder {
        color: var(--text-muted);
    }

    .clear-keyword-btn {
        position: absolute;
        right: 8px;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-tertiary);
        border: none;
        border-radius: 50%;
        font-size: 14px;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .clear-keyword-btn:hover {
        background: var(--danger-color);
        color: white;
    }

    /* 排序按钮（紧凑版） */
    .sort-btn-compact {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 12px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 13px;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .sort-btn-compact:hover {
        border-color: var(--primary-color);
        color: var(--text-primary);
    }

    .sort-btn-compact svg {
        transition: transform 0.2s ease;
    }

    .sort-btn-compact.asc svg {
        transform: rotate(180deg);
    }

    /* 搜索按钮 */
    .btn-search {
        padding: 8px 20px;
    }

    /* 自定义时间范围（紧凑版） */
    .custom-time-range-compact {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-color);
    }

    .custom-time-inputs-compact {
        display: flex;
        align-items: flex-end;
        gap: 12px;
        flex-wrap: wrap;
    }

    .time-input-item {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .time-input-item label {
        font-size: 12px;
        color: var(--text-secondary);
    }

    .time-range-arrow {
        color: var(--text-muted);
        margin-bottom: 4px;
    }

    /* 导出下拉菜单 */
    .card-actions {
        display: flex;
        gap: 8px;
    }

    .export-dropdown {
        position: relative;
    }

    .export-menu {
        position: absolute;
        top: 100%;
        right: 0;
        margin-top: 4px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        z-index: 100;
        display: none;
        min-width: 160px;
        overflow: hidden;
    }

    .export-menu.show {
        display: block;
    }

    .export-menu-item {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        padding: 10px 14px;
        background: none;
        border: none;
        font-size: 13px;
        color: var(--text-primary);
        cursor: pointer;
        transition: background 0.2s ease;
        text-align: left;
    }

    .export-menu-item:hover {
        background: var(--bg-secondary);
    }

    .export-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 24px;
        background: var(--primary-bg);
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        color: var(--primary-color);
    }

    .export-label {
        color: var(--text-secondary);
    }

    /* ========== 日志空状态 ========== */
    .logs-empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .empty-icon {
        opacity: 0.4;
        margin-bottom: 16px;
    }

    .empty-text {
        text-align: center;
    }

    .empty-text h4 {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 8px 0;
    }

    .empty-text p {
        font-size: 14px;
        color: var(--text-muted);
        margin: 0;
    }

    /* ========== 日志表格（新版） ========== */
    .logs-table-container {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
        background: var(--bg-primary);
    }

    .logs-table-new {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    .logs-table-new thead {
        background: var(--bg-secondary);
        border-bottom: 2px solid var(--border-color);
    }

    .logs-table-new th {
        padding: 12px 16px;
        text-align: left;
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .logs-table-new th.col-time { width: 160px; }
    .logs-table-new th.col-level { width: 90px; }
    .logs-table-new th.col-module { width: 120px; }
    .logs-table-new th.col-function { width: 120px; }
    .logs-table-new th.col-line { width: 60px; text-align: center; }
    .logs-table-new th.col-message { min-width: 200px; }

    .logs-table-new tbody tr {
        border-bottom: 1px solid var(--border-color);
        transition: background 0.2s ease;
    }

    .logs-table-new tbody tr:last-child {
        border-bottom: none;
    }

    .logs-table-new tbody tr:hover {
        background: var(--bg-secondary);
    }

    /* 日志行级别背景色 */
    .log-row.level-error {
        background: var(--danger-bg);
    }

    .log-row.level-error:hover {
        background: rgba(239, 68, 68, 0.15);
    }

    .log-row.level-warning {
        background: var(--warning-bg);
    }

    .log-row.level-warning:hover {
        background: rgba(245, 158, 11, 0.15);
    }

    .log-row.level-critical {
        background: rgba(220, 38, 38, 0.1);
    }

    .log-row.level-critical:hover {
        background: rgba(220, 38, 38, 0.15);
    }

    .log-cell {
        padding: 12px 16px;
        vertical-align: top;
    }

    .log-time-cell {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
        color: var(--text-muted);
    }

    .log-level-cell {
        text-align: center;
    }

    .log-level-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        color: white;
    }

    .log-level-tag.level-debug { background: #6b7280; }
    .log-level-tag.level-info { background: #3b82f6; }
    .log-level-tag.level-success { background: #22c55e; }
    .log-level-tag.level-warning { background: #f59e0b; }
    .log-level-tag.level-error { background: #ef4444; }
    .log-level-tag.level-critical { background: #dc2626; }

    .log-module-cell,
    .log-function-cell {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
        color: var(--text-secondary);
    }

    .log-line-cell {
        text-align: center;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
        color: var(--text-muted);
    }

    .log-message-cell {
        cursor: pointer;
    }

    .log-message-wrapper {
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }

    .log-message-text {
        flex: 1;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        color: var(--text-primary);
        word-break: break-word;
    }

    .log-expand-btn {
        flex-shrink: 0;
        color: var(--text-muted);
        transition: transform 0.2s ease;
        margin-top: 2px;
    }

    .log-expand-btn.expanded {
        transform: rotate(180deg);
    }

    /* 日志详情（内联版） */
    .log-detail-inline {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px dashed var(--border-color);
    }

    .detail-block {
        margin-bottom: 12px;
    }

    .detail-block:last-child {
        margin-bottom: 0;
    }

    .detail-block.exception-block {
        background: var(--danger-bg);
        padding: 12px;
        border-radius: var(--radius-sm);
    }

    .detail-label {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .detail-block.exception-block .detail-label {
        color: var(--danger-color);
    }

    .detail-content {
        margin: 0;
        padding: 12px;
        background: var(--bg-primary);
        border-radius: var(--radius-sm);
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
        color: var(--text-primary);
        white-space: pre-wrap;
        word-break: break-word;
        overflow-x: auto;
        max-height: 300px;
        overflow-y: auto;
    }

    /* ========== 分页（紧凑版） ========== */
    .logs-pagination-compact {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 16px;
        padding: 12px 16px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .pagination-info {
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 13px;
        color: var(--text-secondary);
    }

    .pagination-total strong {
        color: var(--text-primary);
        font-weight: 600;
    }

    .pagination-current {
        padding: 4px 10px;
        background: var(--bg-primary);
        border-radius: var(--radius-sm);
        font-size: 12px;
    }

    .pagination-controls {
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .pagination-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 32px;
        height: 32px;
        padding: 0 8px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-sm);
        font-size: 13px;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .pagination-btn:hover:not(.disabled):not(.active) {
        background: var(--bg-tertiary);
        border-color: var(--primary-color);
        color: var(--primary-color);
    }

    .pagination-btn.active {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
        font-weight: 600;
    }

    .pagination-btn.disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .pagination-ellipsis {
        padding: 0 8px;
        color: var(--text-muted);
    }

    /* ========== 健康检查 Tab ========== */
    .health-tab {
        background: var(--bg-primary);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
        padding: 20px;
    }

    .health-detail-card {
        background: var(--bg-primary);
    }

    .health-detail-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
    }

    .health-detail-header h3 {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .health-detail-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
    }

    .detail-section h4 {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 16px 0;
    }

    .detail-items {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .detail-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .detail-label {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .detail-value {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
    }

    .service-detail-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .service-detail-item {
        padding: 12px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
        border-left: 3px solid transparent;
    }

    .service-detail-item.healthy {
        border-left-color: var(--success-color);
    }

    .service-detail-item.unhealthy {
        border-left-color: var(--danger-color);
    }

    .service-detail-item.degraded {
        border-left-color: var(--warning-color);
    }

    .service-detail-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .service-detail-name {
        font-weight: 600;
        color: var(--text-primary);
    }

    .service-detail-status {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: var(--radius-sm);
        background: var(--bg-tertiary);
        color: var(--text-secondary);
    }

    .service-detail-item.healthy .service-detail-status {
        background: var(--success-bg);
        color: var(--success-color);
    }

    .service-detail-item.unhealthy .service-detail-status {
        background: var(--danger-bg);
        color: var(--danger-color);
    }

    .service-detail-item.degraded .service-detail-status {
        background: var(--warning-bg);
        color: var(--warning-color);
    }

    .service-detail-latency {
        font-size: 12px;
        color: var(--text-muted);
    }

    .service-detail-message {
        font-size: 12px;
        color: var(--danger-color);
        margin-top: 8px;
    }

    /* ========== 分页 ========== */
    .logs-pagination {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 16px;
    }

    .pagination-info {
        font-size: 13px;
        color: var(--text-secondary);
    }

    /* ========== 空状态 ========== */
    .empty-state,
    .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        color: var(--text-muted);
        gap: 12px;
    }

    .empty-state svg {
        opacity: 0.4;
    }

    .empty-state p {
        margin: 0;
        font-size: 14px;
    }

    /* ========== 按钮样式增强 ========== */
    .btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: var(--radius-md);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
    }

    .btn-sm {
        padding: 6px 12px;
        font-size: 13px;
    }

    .btn-primary {
        background: var(--primary-color);
        color: white;
    }

    .btn-primary:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }

    .btn-primary:active {
        transform: translateY(0);
    }

    .btn-primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
    }

    .btn-outline {
        background: transparent;
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }

    .btn-outline:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border-color: var(--text-muted);
    }

    .refresh-btn {
        white-space: nowrap;
    }

    /* ========== 表单控件 ========== */
    .form-control {
        padding: 8px 12px;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        font-size: 13px;
        color: var(--text-primary);
        transition: all 0.2s ease;
    }

    .form-control:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* ========== 响应式设计 ========== */
    @media (max-width: 1400px) {
        .logs-table-new th.col-module,
        .logs-table-new th.col-function {
            display: none;
        }
        
        .log-module-cell,
        .log-function-cell {
            display: none;
        }
        
        .logs-table-new th.col-time { width: 140px; }
    }

    @media (max-width: 1200px) {
        .health-grid {
            grid-template-columns: 1fr;
        }

        .services-card,
        .system-card {
            grid-column: 1 / -1;
        }

        .filter-row-compact {
            gap: 12px;
        }

        .filter-item-keyword {
            min-width: 100%;
            order: 1;
        }

        .filter-item-search {
            order: 2;
        }
        
        .logs-table-new th.col-line {
            display: none;
        }
        
        .log-line-cell {
            display: none;
        }
    }

    @media (max-width: 1024px) {
        .resource-gauges {
            grid-template-columns: 1fr;
        }

        .health-detail-grid {
            grid-template-columns: 1fr;
        }
        
        .logs-pagination-compact {
            flex-direction: column;
            gap: 12px;
        }
        
        .pagination-info {
            width: 100%;
            justify-content: center;
        }
        
        .pagination-controls {
            width: 100%;
            justify-content: center;
        }
    }

    @media (max-width: 768px) {
        .filter-row-compact {
            flex-direction: column;
            align-items: stretch;
        }

        .filter-item-compact {
            width: 100%;
        }

        .filter-item-keyword {
            order: 0;
        }

        .time-range-select-wrapper,
        .level-dropdown-btn-compact,
        .sort-btn-compact,
        .form-input-compact {
            width: 100%;
        }

        .custom-time-inputs-compact {
            flex-direction: column;
            align-items: stretch;
        }

        .time-range-arrow {
            display: none;
        }

        .services-grid {
            grid-template-columns: 1fr;
        }

        .tabs-container {
            flex-wrap: wrap;
        }

        .tab-btn {
            flex: 1;
            justify-content: center;
            min-width: 100px;
        }

        .card-header-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
        }

        .card-actions {
            width: 100%;
        }

        .card-actions .export-dropdown {
            width: 100%;
        }

        .card-actions .btn {
            width: 100%;
            justify-content: center;
        }

        .export-menu {
            left: 0;
            right: 0;
            width: 100%;
        }

        /* 移动端日志表格 */
        .logs-table-new thead {
            display: none;
        }

        .logs-table-new tbody tr {
            display: flex;
            flex-direction: column;
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }

        .log-cell {
            padding: 4px 0;
        }

        .log-time-cell::before {
            content: '时间: ';
            color: var(--text-muted);
        }

        .log-level-cell::before {
            content: '级别: ';
            color: var(--text-muted);
            margin-right: 8px;
        }

        .log-module-cell,
        .log-function-cell,
        .log-line-cell {
            display: block;
        }

        .log-module-cell::before {
            content: '模块: ';
            color: var(--text-muted);
        }

        .log-function-cell::before {
            content: '函数: ';
            color: var(--text-muted);
        }

        .log-line-cell::before {
            content: '行号: ';
            color: var(--text-muted);
        }

        .log-message-cell::before {
            content: '消息: ';
            color: var(--text-muted);
            display: block;
            margin-bottom: 4px;
        }

        .log-level-cell {
            display: flex;
            align-items: center;
        }
    }
`;
    document.head.appendChild(monitorStyles);
}

window.MonitorPage = MonitorPage;
window.monitorApi = monitorApi;
