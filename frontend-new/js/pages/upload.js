/**
 * 简历上传筛选模块
 * 提供上传、多条件筛选构建器、实时进度显示功能
 */

const UploadPage = {
    conditions: [],
    conditionGroups: [
        {
            id: 'group_1',
            logic: 'and',
            conditionIds: [],
        },
    ],
    groupLogic: 'and',
    excludeConditionIds: [],
    uploadedFiles: [],
    screeningResult: null,
    ws: null,
    currentTaskId: null,
    TASK_ID_KEY: 'resume_screening_task_id',
    dataLoadedAt: null,
    CACHE_DURATION: 5 * 60 * 1000,

    saveTaskId(taskId) {
        if (taskId) {
            localStorage.setItem(this.TASK_ID_KEY, taskId);
        }
    },

    clearTaskId() {
        localStorage.removeItem(this.TASK_ID_KEY);
    },

    getSavedTaskId() {
        return localStorage.getItem(this.TASK_ID_KEY);
    },

    async render() {
        this.loadDataAsync();
        return this.renderContent();
    },

    async loadDataAsync() {
        const now = Date.now();
        
        if (this.conditions.length > 0 && this.dataLoadedAt) {
            const age = now - this.dataLoadedAt;
            if (age < this.CACHE_DURATION) {
                return;
            }
        }

        try {
            const response = await conditionsApi.getList({ page: 1, page_size: 100 });
            if (response.success) {
                this.conditions = response.data.items || [];
                this.dataLoadedAt = now;
                this.updateConditionBuilder();
            }
        } catch (error) {
            console.error('加载筛选条件失败:', error);
        }
    },

    updateConditionBuilder() {
        const builderContainer = document.querySelector('.condition-builder');
        if (builderContainer) {
            builderContainer.outerHTML = this.renderConditionBuilder();
        }
    },

    /**
     * 渲染页面内容
     */
    renderContent() {
        return `
            <div class="upload-page">
                <div class="upload-container">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">上传简历</h3>
                        </div>
                        <div class="card-body">
                            <div class="upload-area" id="uploadArea">
                                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                    <polyline points="17 8 12 3 7 8"/>
                                    <line x1="12" y1="3" x2="12" y2="15"/>
                                </svg>
                                <div class="upload-title">拖拽文件到此处或点击选择</div>
                                <div class="upload-hint">支持 PDF、DOCX 格式，单个文件最大 10MB，最多 50 个文件</div>
                                <input type="file" id="fileInput" accept=".pdf,.docx,.doc" multiple hidden>
                            </div>

                            <div class="file-list hidden" id="fileList">
                                <div class="file-list-header">
                                    <span>已选择 <span id="fileCount">0</span> 个文件</span>
                                    <button class="btn btn-ghost btn-sm" id="clearAllBtn">清空全部</button>
                                </div>
                                <div class="file-list-items" id="fileListItems"></div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">筛选条件构建器</h3>
                            <button class="btn btn-ghost btn-sm" id="resetConditionsBtn">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                                    <path d="M3 3v5h5"/>
                                </svg>
                                重置
                            </button>
                        </div>
                        <div class="card-body">
                            ${this.renderConditionBuilder()}
                        </div>
                    </div>
                </div>

                <div class="progress-container hidden" id="progressContainer">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">处理进度</h3>
                            <button class="btn btn-ghost btn-sm hidden" id="cancelTaskBtn">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <line x1="15" y1="9" x2="9" y2="15"/>
                                    <line x1="9" y1="9" x2="15" y2="15"/>
                                </svg>
                                取消任务
                            </button>
                        </div>
                        <div class="card-body">
                            <div class="progress-info">
                                <div class="progress-bar-container">
                                    <div class="progress-bar" id="progressBar" style="width: 0%"></div>
                                </div>
                                <div class="progress-text">
                                    <span id="progressText">0%</span>
                                    <span id="progressMessage">准备中...</span>
                                </div>
                            </div>
                            <div class="progress-stats" id="progressStats"></div>
                        </div>
                    </div>
                </div>

                <div class="result-container hidden" id="resultContainer">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">筛选结果</h3>
                        </div>
                        <div class="card-body" id="resultBody">
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 渲染条件构建器
     */
    renderConditionBuilder() {
        const availableConditions = this.conditions.filter(
            c => !this.getAllSelectedConditionIds().includes(c.id)
        );

        return `
            <div class="condition-builder">
                <!-- 条件组列表 -->
                <div class="condition-groups" id="conditionGroups">
                    ${this.conditionGroups.map((group, index) => this.renderConditionGroup(group, index)).join('')}
                </div>

                <!-- 添加条件组按钮 -->
                <button class="btn btn-ghost btn-block" id="addGroupBtn" ${availableConditions.length === 0 ? 'disabled' : ''}>
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    添加条件组
                </button>

                <!-- 组间逻辑 -->
                ${this.conditionGroups.length > 1 ? `
                    <div class="group-logic">
                        <span>组间逻辑：</span>
                        <div class="logic-toggle">
                            <button class="btn btn-sm ${this.groupLogic === 'and' ? 'btn-primary' : 'btn-ghost'}" data-logic="and" onclick="UploadPage.setGroupLogic('and')">
                                AND（全部满足）
                            </button>
                            <button class="btn btn-sm ${this.groupLogic === 'or' ? 'btn-primary' : 'btn-ghost'}" data-logic="or" onclick="UploadPage.setGroupLogic('or')">
                                OR（任一满足）
                            </button>
                        </div>
                    </div>
                ` : ''}

                <!-- 排除条件 -->
                <div class="exclude-conditions">
                    <div class="exclude-header">
                        <span class="exclude-title">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                            </svg>
                            排除条件（NOT）
                        </span>
                        <button class="btn btn-ghost btn-sm" id="addExcludeBtn" ${availableConditions.length === 0 ? 'disabled' : ''} onclick="UploadPage.showExcludeSelect()">
                            + 添加排除
                        </button>
                    </div>
                    <div class="exclude-list" id="excludeList">
                        ${this.renderExcludeConditions()}
                    </div>
                </div>

                <!-- 筛选摘要 -->
                <div class="filter-summary">
                    <div class="summary-text" id="filterSummary">
                        ${this.generateFilterSummary()}
                    </div>
                </div>

                <!-- 提交按钮 -->
                <button class="btn btn-primary btn-lg" id="submitBtn" disabled>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    <span id="submitBtnText">开始筛选</span>
                </button>
            </div>
        `;
    },

    /**
     * 渲染单个条件组
     */
    renderConditionGroup(group, index) {
        const availableConditions = this.conditions.filter(
            c => !this.getAllSelectedConditionIds().includes(c.id) || group.conditionIds.includes(c.id)
        );

        return `
            <div class="condition-group" data-group-id="${group.id}">
                <div class="group-header">
                    <span class="group-label">条件组 ${index + 1}</span>
                    <div class="group-logic-toggle">
                        <button class="btn btn-xs ${group.logic === 'and' ? 'btn-primary' : 'btn-ghost'}" 
                                onclick="UploadPage.setGroupConditionLogic('${group.id}', 'and')">
                            AND
                        </button>
                        <button class="btn btn-xs ${group.logic === 'or' ? 'btn-primary' : 'btn-ghost'}" 
                                onclick="UploadPage.setGroupConditionLogic('${group.id}', 'or')">
                            OR
                        </button>
                    </div>
                    ${this.conditionGroups.length > 1 ? `
                        <button class="btn btn-icon btn-ghost" onclick="UploadPage.removeGroup('${group.id}')" title="删除条件组">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                    ` : ''}
                </div>
                <div class="group-conditions">
                    ${group.conditionIds.map(conditionId => {
                        const condition = this.conditions.find(c => c.id === conditionId);
                        return condition ? `
                            <div class="selected-condition">
                                <span class="condition-name">${this.escapeHtml(condition.name)}</span>
                                <button class="btn btn-icon btn-ghost" onclick="UploadPage.removeConditionFromGroup('${group.id}', '${conditionId}')">
                                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                </button>
                            </div>
                        ` : '';
                    }).join('')}
                    ${availableConditions.length > 0 ? `
                        <select class="form-control form-control-sm condition-select" 
                                onchange="UploadPage.addConditionToGroup('${group.id}', this.value)">
                            <option value="">+ 添加条件</option>
                            ${availableConditions.map(c => `
                                <option value="${c.id}">${this.escapeHtml(c.name)}</option>
                            `).join('')}
                        </select>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * 渲染排除条件列表
     */
    renderExcludeConditions() {
        if (this.excludeConditionIds.length === 0) {
            return '<div class="empty-hint">未设置排除条件</div>';
        }
        
        return this.excludeConditionIds.map(id => {
            const condition = this.conditions.find(c => c.id === id);
            if (!condition) return '';
            return '<div class="exclude-item">' +
                '<span>' + this.escapeHtml(condition.name) + '</span>' +
                '<button class="btn btn-icon btn-ghost" onclick="UploadPage.removeExclude(\'' + id + '\')">' +
                '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">' +
                '<line x1="18" y1="6" x2="6" y2="18"/>' +
                '<line x1="6" y1="6" x2="18" y2="18"/>' +
                '</svg>' +
                '</button>' +
                '</div>';
        }).join('');
    },

    /**
     * 获取所有已选中的条件 ID
     */
    getAllSelectedConditionIds() {
        const allIds = new Set();
        this.conditionGroups.forEach(group => {
            group.conditionIds.forEach(id => allIds.add(id));
        });
        this.excludeConditionIds.forEach(id => allIds.add(id));
        return Array.from(allIds);
    },

    /**
     * 设置组间逻辑
     */
    setGroupLogic(logic) {
        this.groupLogic = logic;
        this.refreshConditionBuilder();
    },

    /**
     * 设置条件组内逻辑
     */
    setGroupConditionLogic(groupId, logic) {
        const group = this.conditionGroups.find(g => g.id === groupId);
        if (group) {
            group.logic = logic;
            this.refreshConditionBuilder();
        }
    },

    /**
     * 添加条件组
     */
    addConditionGroup() {
        const newGroup = {
            id: `group_${Date.now()}`,
            logic: 'and',
            conditionIds: [],
        };
        this.conditionGroups.push(newGroup);
        this.refreshConditionBuilder();
    },

    /**
     * 删除条件组
     */
    removeGroup(groupId) {
        this.conditionGroups = this.conditionGroups.filter(g => g.id !== groupId);
        if (this.conditionGroups.length === 0) {
            this.conditionGroups = [{
                id: 'group_1',
                logic: 'and',
                conditionIds: [],
            }];
        }
        this.refreshConditionBuilder();
    },

    /**
     * 添加条件到组
     */
    addConditionToGroup(groupId, conditionId) {
        if (!conditionId) return;
        
        const group = this.conditionGroups.find(g => g.id === groupId);
        if (group && !group.conditionIds.includes(conditionId)) {
            group.conditionIds.push(conditionId);
            this.refreshConditionBuilder();
        }
    },

    /**
     * 从组中移除条件
     */
    removeConditionFromGroup(groupId, conditionId) {
        const group = this.conditionGroups.find(g => g.id === groupId);
        if (group) {
            group.conditionIds = group.conditionIds.filter(id => id !== conditionId);
            this.refreshConditionBuilder();
        }
    },

    /**
     * 显示排除条件选择
     */
    showExcludeSelect() {
        const availableConditions = this.conditions.filter(
            c => !this.getAllSelectedConditionIds().includes(c.id)
        );
        
        if (availableConditions.length === 0) {
            UI.toast('没有可用的筛选条件', 'warning');
            return;
        }

        // 创建选择弹窗
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal modal-sm">
                <div class="modal-header">
                    <h3>选择排除条件</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="condition-options">
                        ${availableConditions.map(c => `
                            <div class="condition-option" onclick="UploadPage.addExclude('${c.id}'); this.closest('.modal-overlay').remove();">
                                <span>${this.escapeHtml(c.name)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        // 添加 active 类以显示模态框
        requestAnimationFrame(() => modal.classList.add('active'));
    },

    /**
     * 添加排除条件
     */
    addExclude(conditionId) {
        if (!this.excludeConditionIds.includes(conditionId)) {
            this.excludeConditionIds.push(conditionId);
            this.refreshConditionBuilder();
        }
    },

    /**
     * 移除排除条件
     */
    removeExclude(conditionId) {
        this.excludeConditionIds = this.excludeConditionIds.filter(id => id !== conditionId);
        this.refreshConditionBuilder();
    },

    /**
     * 重置条件构建器
     */
    resetConditionBuilder() {
        this.conditionGroups = [{
            id: 'group_1',
            logic: 'and',
            conditionIds: [],
        }];
        this.groupLogic = 'and';
        this.excludeConditionIds = [];
        this.refreshConditionBuilder();
    },

    /**
     * 刷新条件构建器
     */
    refreshConditionBuilder() {
        const cardBody = document.querySelector('.condition-builder')?.closest('.card-body');
        if (cardBody) {
            cardBody.innerHTML = this.renderConditionBuilder();
            this.updateSubmitButton();
            this.initEvents();
        }
    },

    /**
     * 生成筛选摘要
     */
    generateFilterSummary() {
        const parts = [];
        
        // 条件组摘要
        const groupSummaries = this.conditionGroups
            .filter(g => g.conditionIds.length > 0)
            .map(group => {
                const names = group.conditionIds.map(id => {
                    const c = this.conditions.find(cond => cond.id === id);
                    return c ? c.name : id;
                });
                return `(${names.join(` ${group.logic.toUpperCase()} `)})`;
            });

        if (groupSummaries.length > 0) {
            parts.push(groupSummaries.join(` ${this.groupLogic.toUpperCase()} `));
        }

        // 排除条件摘要
        if (this.excludeConditionIds.length > 0) {
            const excludeNames = this.excludeConditionIds.map(id => {
                const c = this.conditions.find(cond => cond.id === id);
                return c ? c.name : id;
            });
            parts.push(`NOT (${excludeNames.join(' OR ')})`);
        }

        return parts.length > 0 
            ? `筛选逻辑：${parts.join(' ')}`
            : '未设置筛选条件（仅解析简历）';
    },

    /**
     * 获取筛选配置
     */
    getFilterConfig() {
        const hasConditions = this.conditionGroups.some(g => g.conditionIds.length > 0);
        
        if (!hasConditions && this.excludeConditionIds.length === 0) {
            return null;
        }

        return {
            groups: this.conditionGroups
                .filter(g => g.conditionIds.length > 0)
                .map(g => ({
                    logic: g.logic,
                    condition_ids: g.conditionIds,
                })),
            group_logic: this.groupLogic,
            exclude_condition_ids: this.excludeConditionIds,
        };
    },

    /**
     * 初始化页面事件
     */
    initEvents() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const clearAllBtn = document.getElementById('clearAllBtn');
        const submitBtn = document.getElementById('submitBtn');
        const cancelTaskBtn = document.getElementById('cancelTaskBtn');
        const addGroupBtn = document.getElementById('addGroupBtn');
        const resetConditionsBtn = document.getElementById('resetConditionsBtn');

        // 点击上传区域
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());

            // 拖拽上传
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = Array.from(e.dataTransfer.files);
                if (files.length > 0) {
                    this.handleFilesSelect(files);
                }
            });

            // 文件选择
            fileInput.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                if (files.length > 0) {
                    this.handleFilesSelect(files);
                }
            });
        }

        // 清空全部
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllFiles());
        }

        // 添加条件组
        if (addGroupBtn) {
            addGroupBtn.addEventListener('click', () => this.addConditionGroup());
        }

        // 重置条件
        if (resetConditionsBtn) {
            resetConditionsBtn.addEventListener('click', () => this.resetConditionBuilder());
        }

        // 提交按钮
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitScreening());
        }

        // 取消任务
        if (cancelTaskBtn) {
            cancelTaskBtn.addEventListener('click', () => this.cancelTask());
        }

        // 初始化 WebSocket
        this.initWebSocket();

        // 恢复未完成的任务进度
        this.restoreTaskProgress();
    },

    /**
     * 恢复任务进度显示
     */
    async restoreTaskProgress() {
        const savedTaskId = this.getSavedTaskId();
        if (!savedTaskId) {
            return;
        }

        try {
            const response = await talentsApi.getTaskStatus(savedTaskId);
            if (response.success && response.data) {
                const taskData = response.data;
                const status = taskData.status;

                if (status === 'pending' || status === 'running') {
                    this.currentTaskId = savedTaskId;

                    const progressContainer = document.getElementById('progressContainer');
                    const resultContainer = document.getElementById('resultContainer');
                    const cancelTaskBtn = document.getElementById('cancelTaskBtn');

                    if (progressContainer) progressContainer.classList.remove('hidden');
                    if (resultContainer) resultContainer.classList.add('hidden');
                    if (cancelTaskBtn && status === 'running') cancelTaskBtn.classList.remove('hidden');

                    this.updateProgressUI(taskData);

                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({
                            type: 'subscribe',
                            task_id: this.currentTaskId
                        }));
                    }
                } else {
                    this.clearTaskId();
                }
            }
        } catch (error) {
            console.error('恢复任务进度失败:', error);
            this.clearTaskId();
        }
    },

    /**
     * 初始化 WebSocket 连接
     */
    initWebSocket() {
        const wsUrl = 'ws://localhost:8000/ws/tasks';
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket 连接已建立');
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket 连接已关闭');
                // 尝试重连
                setTimeout(() => this.initWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
            };
        } catch (error) {
            console.error('WebSocket 初始化失败:', error);
        }
    },

    /**
     * 处理 WebSocket 消息
     */
    handleWebSocketMessage(message) {
        if (message.type === 'task_update' && message.task_id === this.currentTaskId) {
            this.updateProgressUI(message.data);
        }
    },

    /**
     * 处理文件选择
     */
    handleFilesSelect(files) {
        const allowedTypes = ['pdf', 'docx', 'doc'];
        const validFiles = [];
        const errors = [];

        for (const file of files) {
            const ext = file.name.split('.').pop().toLowerCase();
            
            if (!allowedTypes.includes(ext)) {
                errors.push(`${file.name}: 不支持的格式`);
                continue;
            }

            if (file.size > 10 * 1024 * 1024) {
                errors.push(`${file.name}: 文件过大`);
                continue;
            }

            validFiles.push(file);
        }

        if (errors.length > 0) {
            UI.toast(`部分文件无效: ${errors.slice(0, 3).join(', ')}${errors.length > 3 ? '...' : ''}`, 'warning');
        }

        if (validFiles.length > 50) {
            UI.toast('最多支持 50 个文件，已自动截取前 50 个', 'warning');
            validFiles.splice(50);
        }

        // 合并到现有文件列表
        for (const file of validFiles) {
            if (!this.uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
                this.uploadedFiles.push(file);
            }
        }

        this.showFileList();
        this.updateSubmitButton();
    },

    /**
     * 显示文件列表
     */
    showFileList() {
        const uploadArea = document.getElementById('uploadArea');
        const fileList = document.getElementById('fileList');
        const fileCount = document.getElementById('fileCount');
        const fileListItems = document.getElementById('fileListItems');

        if (this.uploadedFiles.length === 0) {
            if (uploadArea) uploadArea.classList.remove('hidden');
            if (fileList) fileList.classList.add('hidden');
            return;
        }

        if (uploadArea) uploadArea.classList.add('hidden');
        if (fileList) fileList.classList.remove('hidden');
        if (fileCount) fileCount.textContent = this.uploadedFiles.length;

        if (fileListItems) {
            fileListItems.innerHTML = this.uploadedFiles.map((file, index) => `
                <div class="file-item">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <div class="file-item-info">
                        <div class="file-item-name">${this.escapeHtml(file.name)}</div>
                        <div class="file-item-size">${UI.formatFileSize(file.size)}</div>
                    </div>
                    <button class="btn btn-ghost btn-icon" onclick="UploadPage.removeFile(${index})" title="移除">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
            `).join('');
        }
    },

    /**
     * 移除单个文件
     */
    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.showFileList();
        this.updateSubmitButton();
    },

    /**
     * 清空所有文件
     */
    clearAllFiles() {
        this.uploadedFiles = [];
        this.screeningResult = null;
        this.currentTaskId = null;
        this.clearTaskId();

        const uploadArea = document.getElementById('uploadArea');
        const fileList = document.getElementById('fileList');
        const fileInput = document.getElementById('fileInput');
        const resultContainer = document.getElementById('resultContainer');
        const progressContainer = document.getElementById('progressContainer');

        if (uploadArea) uploadArea.classList.remove('hidden');
        if (fileList) fileList.classList.add('hidden');
        if (fileInput) fileInput.value = '';
        if (resultContainer) resultContainer.classList.add('hidden');
        if (progressContainer) progressContainer.classList.add('hidden');

        this.updateSubmitButton();
    },

    /**
     * 更新提交按钮状态
     */
    updateSubmitButton() {
        const submitBtn = document.getElementById('submitBtn');
        const submitBtnText = document.getElementById('submitBtnText');
        
        if (submitBtn) {
            submitBtn.disabled = this.uploadedFiles.length === 0;
        }
        
        if (submitBtnText) {
            const count = this.uploadedFiles.length;
            submitBtnText.textContent = count > 0 ? `开始筛选 (${count} 个文件)` : '开始筛选';
        }
    },

    /**
     * 提交筛选
     */
    async submitScreening() {
        if (this.uploadedFiles.length === 0) {
            UI.toast('请先上传简历文件', 'warning');
            return;
        }

        try {
            // 显示进度容器
            const progressContainer = document.getElementById('progressContainer');
            const resultContainer = document.getElementById('resultContainer');
            const cancelTaskBtn = document.getElementById('cancelTaskBtn');
            
            if (progressContainer) progressContainer.classList.remove('hidden');
            if (resultContainer) resultContainer.classList.add('hidden');
            if (cancelTaskBtn) cancelTaskBtn.classList.remove('hidden');

            // 重置进度
            this.updateProgressUI({
                status: 'pending',
                progress: { current: 0, total: this.uploadedFiles.length, percentage: 0, message: '正在提交...' }
            });

            // 获取第一个条件 ID（向后兼容）
            const firstConditionId = this.conditionGroups[0]?.conditionIds[0] || null;

            // 统一使用批量上传接口
            const response = await talentsApi.batchUpload(
                this.uploadedFiles,
                firstConditionId
            );

            if (response.success) {
                this.currentTaskId = response.data.task_id;
                this.saveTaskId(this.currentTaskId);
                
                // 订阅任务更新
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'subscribe',
                        task_id: this.currentTaskId
                    }));
                }
                
                UI.toast(`上传任务已创建，共 ${response.data.file_count} 个文件`, 'success');
            } else {
                UI.toast(response.message || '上传失败', 'error');
            }

        } catch (error) {
            console.error('简历筛选失败:', error);
            UI.toast(error.message || '简历筛选失败', 'error');
        }
    },

    /**
     * 更新进度 UI
     */
    updateProgressUI(taskData) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const progressMessage = document.getElementById('progressMessage');
        const progressStats = document.getElementById('progressStats');
        const cancelTaskBtn = document.getElementById('cancelTaskBtn');

        const progress = taskData.progress || {};
        const percentage = progress.percentage || 0;

        if (progressBar) progressBar.style.width = `${percentage}%`;
        if (progressText) progressText.textContent = `${percentage.toFixed(1)}%`;
        if (progressMessage) progressMessage.textContent = progress.message || '处理中...';

        // 更新状态样式
        if (progressBar) {
            progressBar.classList.remove('progress-bar-success', 'progress-bar-danger');
            if (taskData.status === 'completed') {
                progressBar.classList.add('progress-bar-success');
            } else if (taskData.status === 'failed') {
                progressBar.classList.add('progress-bar-danger');
            }
        }

        // 显示统计信息
        if (progressStats && taskData.status === 'completed') {
            const result = taskData.result || {};
            progressStats.innerHTML = `
                <div class="stat-item success">
                    <span class="stat-value">${result.success || 0}</span>
                    <span class="stat-label">成功</span>
                </div>
                <div class="stat-item warning">
                    <span class="stat-value">${result.duplicate || 0}</span>
                    <span class="stat-label">重复</span>
                </div>
                <div class="stat-item danger">
                    <span class="stat-value">${result.failed || 0}</span>
                    <span class="stat-label">失败</span>
                </div>
            `;
        }

        // 任务完成或失败时隐藏取消按钮
        if (cancelTaskBtn && (taskData.status === 'completed' || taskData.status === 'failed' || taskData.status === 'cancelled')) {
            cancelTaskBtn.classList.add('hidden');
            this.clearTaskId();
        }

        // 任务完成时显示结果
        if (taskData.status === 'completed') {
            this.showResult(taskData.result);
        }
    },

    /**
     * 取消任务
     */
    async cancelTask() {
        if (!this.currentTaskId) return;

        try {
            const response = await talentsApi.cancelTask(this.currentTaskId);
            if (response.success) {
                UI.toast('任务已取消', 'success');
            }
        } catch (error) {
            UI.toast(error.message || '取消失败', 'error');
        }
    },

    /**
     * 显示筛选结果
     */
    showResult(result) {
        const resultContainer = document.getElementById('resultContainer');
        const resultBody = document.getElementById('resultBody');
        const progressContainer = document.getElementById('progressContainer');

        if (!resultContainer || !resultBody) return;

        if (progressContainer) progressContainer.classList.add('hidden');
        resultContainer.classList.remove('hidden');

        const results = result.results || [];

        resultBody.innerHTML = `
            <div class="batch-result-header">
                <div class="batch-stat success">
                    <span class="stat-value">${result.success || 0}</span>
                    <span class="stat-label">成功</span>
                </div>
                <div class="batch-stat warning">
                    <span class="stat-value">${result.duplicate || 0}</span>
                    <span class="stat-label">重复</span>
                </div>
                <div class="batch-stat danger">
                    <span class="stat-value">${result.failed || 0}</span>
                    <span class="stat-label">失败</span>
                </div>
            </div>

            ${results.length > 0 ? `
                <div class="batch-result-list">
                    <div class="list-header">
                        <span>处理详情</span>
                    </div>
                    <div class="list-items">
                        ${results.map(r => `
                            <div class="list-item ${r.success ? 'success' : 'danger'}">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    ${r.success 
                                        ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'
                                        : '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
                                    }
                                </svg>
                                <span class="item-name">${this.escapeHtml(r.filename)}</span>
                                <span class="item-status">${r.success ? (r.is_qualified ? '通过' : '未通过') : (r.error || '失败')}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <div class="result-actions">
                <button class="btn btn-secondary" onclick="UploadPage.clearAllFiles()">
                    继续上传
                </button>
                <a href="#/talents" class="btn btn-primary">
                    查看人才列表
                </a>
            </div>
        `;
    },

    /**
     * HTML 转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

// 添加页面特定样式
if (!document.getElementById('upload-styles')) {
    const uploadStyles = document.createElement('style');
    uploadStyles.id = 'upload-styles';
    uploadStyles.textContent = `
    .upload-page {
        max-width: 900px;
        margin: 0 auto;
    }

    .upload-container {
        display: grid;
        gap: 20px;
        margin-bottom: 20px;
    }

    .file-list {
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        padding: 16px;
    }

    .file-list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-weight: 500;
    }

    .file-list-items {
        max-height: 300px;
        overflow-y: auto;
    }

    .file-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        background-color: var(--bg-primary);
        border-radius: var(--radius-sm);
        margin-bottom: 8px;
    }

    .file-item:last-child {
        margin-bottom: 0;
    }

    .file-item-info {
        flex: 1;
        min-width: 0;
    }

    .file-item-name {
        font-weight: 500;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .file-item-size {
        font-size: 12px;
        color: var(--text-secondary);
    }

    /* 条件构建器样式 */
    .condition-builder {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .condition-groups {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .condition-group {
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        padding: 12px;
        border: 1px solid var(--border-color);
    }

    .group-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }

    .group-label {
        font-weight: 500;
        color: var(--text-primary);
    }

    .group-logic-toggle {
        display: flex;
        gap: 4px;
        margin-left: auto;
    }

    .btn-xs {
        padding: 2px 8px;
        font-size: 11px;
    }

    .group-conditions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .selected-condition {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        background-color: var(--primary-bg);
        color: var(--primary-color);
        border-radius: var(--radius-sm);
        font-size: 13px;
    }

    .condition-name {
        max-width: 150px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .condition-select {
        max-width: 200px;
        font-size: 13px;
    }

    .form-control-sm {
        padding: 6px 10px;
        font-size: 13px;
    }

    .group-logic {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .logic-toggle {
        display: flex;
        gap: 4px;
    }

    .exclude-conditions {
        padding: 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        border: 1px dashed var(--danger-color);
    }

    .exclude-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .exclude-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
        color: var(--danger-color);
    }

    .exclude-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .exclude-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        background-color: var(--danger-bg);
        color: var(--danger-color);
        border-radius: var(--radius-sm);
        font-size: 13px;
    }

    .empty-hint {
        color: var(--text-secondary);
        font-size: 13px;
    }

    .filter-summary {
        padding: 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        border-left: 3px solid var(--primary-color);
    }

    .summary-text {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .btn-block {
        width: 100%;
        justify-content: center;
    }

    /* 弹窗样式 */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-sm {
        max-width: 400px;
    }

    .condition-options {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .condition-option {
        padding: 10px 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: background-color 0.2s;
    }

    .condition-option:hover {
        background-color: var(--primary-bg);
        color: var(--primary-color);
    }

    /* 进度条样式 */
    .progress-container {
        margin-bottom: 20px;
    }

    .progress-info {
        margin-bottom: 16px;
    }

    .progress-bar-container {
        height: 8px;
        background-color: var(--bg-secondary);
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 8px;
    }

    .progress-bar {
        height: 100%;
        background-color: var(--primary-color);
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .progress-bar-success {
        background-color: var(--success-color);
    }

    .progress-bar-danger {
        background-color: var(--danger-color);
    }

    .progress-text {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        color: var(--text-secondary);
    }

    .progress-stats {
        display: flex;
        gap: 16px;
        justify-content: center;
    }

    .stat-item {
        text-align: center;
        padding: 12px 24px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .stat-item.success {
        color: var(--success-color);
    }

    .stat-item.warning {
        color: var(--warning-color);
    }

    .stat-item.danger {
        color: var(--danger-color);
    }

    .stat-value {
        display: block;
        font-size: 24px;
        font-weight: 600;
    }

    .stat-label {
        font-size: 13px;
        opacity: 0.8;
    }

    .result-container {
        margin-top: 20px;
    }

    .result-header {
        text-align: center;
        padding: 32px;
        border-radius: var(--radius-md);
        margin-bottom: 24px;
    }

    .result-header.success {
        background-color: var(--success-bg);
        color: var(--success-color);
    }

    .result-header.danger {
        background-color: var(--danger-bg);
        color: var(--danger-color);
    }

    .result-icon {
        margin-bottom: 12px;
    }

    .result-status {
        font-size: 20px;
        font-weight: 600;
    }

    .result-details {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }

    .result-details .detail-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .result-details .detail-item.full-width {
        grid-column: span 2;
    }

    .result-details .detail-label {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .result-details .detail-value {
        font-weight: 500;
        color: var(--text-primary);
    }

    .result-actions {
        display: flex;
        justify-content: center;
        gap: 12px;
    }

    .batch-result-header {
        display: flex;
        gap: 16px;
        justify-content: center;
        margin-bottom: 24px;
    }

    .batch-stat {
        text-align: center;
        padding: 16px 32px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .batch-stat.success {
        color: var(--success-color);
    }

    .batch-stat.warning {
        color: var(--warning-color);
    }

    .batch-stat.danger {
        color: var(--danger-color);
    }

    .batch-result-list {
        margin-bottom: 24px;
    }

    .batch-result-list .list-header {
        font-weight: 500;
        margin-bottom: 12px;
    }

    .batch-result-list .list-items {
        max-height: 300px;
        overflow-y: auto;
    }

    .batch-result-list .list-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-sm);
        margin-bottom: 4px;
        font-size: 13px;
    }

    .batch-result-list .list-item.success {
        color: var(--success-color);
    }

    .batch-result-list .list-item.danger {
        color: var(--danger-color);
    }

    .batch-result-list .item-name {
        flex: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .batch-result-list .item-status {
        font-size: 12px;
        opacity: 0.8;
    }

    @media (max-width: 768px) {
        .result-details {
            grid-template-columns: 1fr;
        }

        .result-details .detail-item.full-width {
            grid-column: span 1;
        }

        .batch-result-header {
            flex-direction: column;
        }

        .batch-stat {
            padding: 12px 24px;
        }
    }
`;
    document.head.appendChild(uploadStyles);
}

document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'upload') {
        UploadPage.initEvents();
    }
});

window.UploadPage = UploadPage;
