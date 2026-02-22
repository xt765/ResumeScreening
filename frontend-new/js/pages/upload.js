/**
 * 简历上传筛选模块
 * 提供文件上传、选择筛选条件、显示筛选结果功能
 */

const UploadPage = {
    // 筛选条件列表
    conditions: [],
    // 选中的筛选条件
    selectedConditionId: null,
    // 上传的文件
    uploadedFile: null,
    // 筛选结果
    screeningResult: null,

    /**
     * 渲染页面
     */
    async render() {
        await this.loadConditions();
        return this.renderContent();
    },

    /**
     * 加载筛选条件列表
     */
    async loadConditions() {
        try {
            const response = await conditionsApi.getList({ page: 1, page_size: 100 });
            if (response.success) {
                this.conditions = response.data.items || [];
            }
        } catch (error) {
            console.error('加载筛选条件失败:', error);
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
                                <div class="upload-title">拖拽文件到此处或点击上传</div>
                                <div class="upload-hint">支持 PDF、DOCX 格式，最大 10MB</div>
                                <input type="file" id="fileInput" accept=".pdf,.docx,.doc" hidden>
                            </div>

                            <div class="file-info hidden" id="fileInfo">
                                <div class="file-preview">
                                    <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                    </svg>
                                </div>
                                <div class="file-details">
                                    <div class="file-name" id="fileName"></div>
                                    <div class="file-size" id="fileSize"></div>
                                </div>
                                <button class="btn btn-ghost btn-icon" id="removeFile" title="移除文件">
                                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">筛选设置</h3>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label class="form-label">选择筛选条件</label>
                                <select class="form-control" id="conditionSelect">
                                    <option value="">不使用筛选条件（仅解析简历）</option>
                                    ${this.conditions.map(c => `
                                        <option value="${c.id}">${this.escapeHtml(c.name)}</option>
                                    `).join('')}
                                </select>
                                <div class="form-hint">选择筛选条件后，系统将自动判断候选人是否符合要求</div>
                            </div>

                            <button class="btn btn-primary btn-lg" id="submitBtn" disabled>
                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <polyline points="22 4 12 14.01 9 11.01"/>
                                </svg>
                                开始筛选
                            </button>
                        </div>
                    </div>
                </div>

                <div class="result-container hidden" id="resultContainer">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">筛选结果</h3>
                        </div>
                        <div class="card-body" id="resultBody">
                            <!-- 结果将在这里显示 -->
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 初始化页面事件
     */
    initEvents() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const removeFile = document.getElementById('removeFile');
        const submitBtn = document.getElementById('submitBtn');
        const conditionSelect = document.getElementById('conditionSelect');

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
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });

            // 文件选择
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0]);
                }
            });
        }

        // 移除文件
        if (removeFile) {
            removeFile.addEventListener('click', () => this.removeFile());
        }

        // 筛选条件选择
        if (conditionSelect) {
            conditionSelect.addEventListener('change', (e) => {
                this.selectedConditionId = e.target.value || null;
            });
        }

        // 提交按钮
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitScreening());
        }
    },

    /**
     * 处理文件选择
     */
    handleFileSelect(file) {
        // 验证文件类型
        const allowedTypes = ['pdf', 'docx', 'doc'];
        const ext = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(ext)) {
            UI.toast('不支持的文件格式，请上传 PDF 或 DOCX 文件', 'error');
            return;
        }

        // 验证文件大小（10MB）
        if (file.size > 10 * 1024 * 1024) {
            UI.toast('文件大小超过限制（最大 10MB）', 'error');
            return;
        }

        this.uploadedFile = file;
        this.showFileInfo(file);
        this.updateSubmitButton();
    },

    /**
     * 显示文件信息
     */
    showFileInfo(file) {
        const uploadArea = document.getElementById('uploadArea');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');

        if (uploadArea) uploadArea.classList.add('hidden');
        if (fileInfo) fileInfo.classList.remove('hidden');
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = UI.formatFileSize(file.size);
    },

    /**
     * 移除文件
     */
    removeFile() {
        this.uploadedFile = null;
        this.screeningResult = null;

        const uploadArea = document.getElementById('uploadArea');
        const fileInfo = document.getElementById('fileInfo');
        const fileInput = document.getElementById('fileInput');
        const resultContainer = document.getElementById('resultContainer');

        if (uploadArea) uploadArea.classList.remove('hidden');
        if (fileInfo) fileInfo.classList.add('hidden');
        if (fileInput) fileInput.value = '';
        if (resultContainer) resultContainer.classList.add('hidden');

        this.updateSubmitButton();
    },

    /**
     * 更新提交按钮状态
     */
    updateSubmitButton() {
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = !this.uploadedFile;
        }
    },

    /**
     * 提交筛选
     */
    async submitScreening() {
        if (!this.uploadedFile) {
            UI.toast('请先上传简历文件', 'warning');
            return;
        }

        try {
            UI.showLoading();
            const response = await talentsApi.uploadAndScreen(
                this.uploadedFile,
                this.selectedConditionId
            );

            if (response.success) {
                this.screeningResult = response.data;
                this.showResult(response.data);
                UI.toast('简历筛选完成', 'success');
            }
        } catch (error) {
            console.error('简历筛选失败:', error);
            UI.toast(error.message || '简历筛选失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 显示筛选结果
     */
    showResult(result) {
        const resultContainer = document.getElementById('resultContainer');
        const resultBody = document.getElementById('resultBody');

        if (!resultContainer || !resultBody) return;

        resultContainer.classList.remove('hidden');

        const isQualified = result.is_qualified;
        const statusClass = isQualified ? 'success' : 'danger';
        const statusText = isQualified ? '通过筛选' : '未通过筛选';
        const statusIcon = isQualified 
            ? '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
            : '<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';

        resultBody.innerHTML = `
            <div class="result-header ${statusClass}">
                <div class="result-icon">${statusIcon}</div>
                <div class="result-status">${statusText}</div>
            </div>

            <div class="result-details">
                <div class="detail-item">
                    <span class="detail-label">人才 ID</span>
                    <span class="detail-value">${result.talent_id || '-'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">处理状态</span>
                    <span class="detail-value">${result.workflow_status || '-'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">处理耗时</span>
                    <span class="detail-value">${result.processing_time ? result.processing_time.toFixed(2) + 's' : '-'}</span>
                </div>
                ${result.qualification_reason ? `
                    <div class="detail-item full-width">
                        <span class="detail-label">筛选原因</span>
                        <span class="detail-value">${this.escapeHtml(result.qualification_reason)}</span>
                    </div>
                ` : ''}
            </div>

            <div class="result-actions">
                <button class="btn btn-secondary" onclick="UploadPage.removeFile()">
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
const uploadStyles = document.createElement('style');
uploadStyles.textContent = `
    .upload-page {
        max-width: 800px;
        margin: 0 auto;
    }

    .upload-container {
        display: grid;
        gap: 20px;
        margin-bottom: 20px;
    }

    .file-info {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .file-preview {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: var(--primary-bg);
        color: var(--primary-color);
        border-radius: var(--radius-md);
    }

    .file-details {
        flex: 1;
    }

    .file-name {
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .file-size {
        font-size: 13px;
        color: var(--text-secondary);
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

    @media (max-width: 768px) {
        .result-details {
            grid-template-columns: 1fr;
        }

        .result-details .detail-item.full-width {
            grid-column: span 1;
        }
    }
`;
document.head.appendChild(uploadStyles);

// 页面加载后初始化事件
document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'upload') {
        setTimeout(() => UploadPage.initEvents(), 100);
    }
});

// 监听路由变化
window.addEventListener('hashchange', () => {
    if (AppState.currentPage === 'upload') {
        setTimeout(() => UploadPage.initEvents(), 100);
    }
});

window.UploadPage = UploadPage;
