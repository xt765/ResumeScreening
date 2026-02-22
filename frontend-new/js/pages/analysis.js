/**
 * 数据分析模块
 * 提供 RAG 智能查询、统计分析、数据导出功能
 */

const AnalysisPage = {
    queryResults: [],
    statistics: null,
    dataLoadedAt: null,
    CACHE_DURATION: 5 * 60 * 1000,

    async render() {
        this.loadDataAsync();
        return this.renderContent();
    },

    async loadDataAsync() {
        const now = Date.now();
        
        if (this.statistics && this.dataLoadedAt) {
            const age = now - this.dataLoadedAt;
            if (age < this.CACHE_DURATION) {
                return;
            }
        }

        try {
            const response = await analysisApi.getStatistics();
            if (response.success) {
                this.statistics = response.data;
                this.dataLoadedAt = now;
                this.updateStatistics();
            }
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    updateStatistics() {
        const statsContainer = document.querySelector('.stats-summary');
        if (statsContainer && this.statistics) {
            statsContainer.outerHTML = this.renderStatsSummary();
        }
    },

    clearCache() {
        this.dataLoadedAt = null;
    },

    /**
     * 渲染页面内容
     */
    renderContent() {
        return `
            <div class="analysis-page">
                <div class="analysis-grid">
                    <!-- RAG 智能查询 -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">RAG 智能查询</h3>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label class="form-label">查询内容</label>
                                <textarea class="form-control" id="queryInput" rows="3" 
                                          placeholder="输入查询内容，如：有 3 年以上 Python 开发经验的候选人"></textarea>
                            </div>
                            <div class="query-options">
                                <div class="form-group">
                                    <label class="form-label">返回数量</label>
                                    <select class="form-control" id="topKSelect">
                                        <option value="5">5 条</option>
                                        <option value="10">10 条</option>
                                        <option value="15">15 条</option>
                                        <option value="20">20 条</option>
                                    </select>
                                </div>
                                <button class="btn btn-primary" id="queryBtn">
                                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="11" cy="11" r="8"/>
                                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                                    </svg>
                                    查询
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- 统计分析 -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">统计分析</h3>
                        </div>
                        <div class="card-body">
                            ${this.renderStatistics()}
                        </div>
                    </div>
                </div>

                <!-- 查询结果 -->
                <div class="card mt-3" id="resultsCard" style="display: none;">
                    <div class="card-header">
                        <h3 class="card-title">查询结果</h3>
                        <span class="result-count" id="resultCount"></span>
                    </div>
                    <div class="card-body" id="resultsBody">
                        <!-- 结果将在这里显示 -->
                    </div>
                </div>

                <!-- 数据导出 -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h3 class="card-title">数据导出</h3>
                    </div>
                    <div class="card-body">
                        <div class="export-options">
                            <div class="export-item">
                                <div class="export-info">
                                    <div class="export-title">导出人才数据</div>
                                    <div class="export-desc">导出所有人才信息为 JSON 格式</div>
                                </div>
                                <button class="btn btn-secondary" id="exportTalents">
                                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                        <polyline points="7 10 12 15 17 10"/>
                                        <line x1="12" y1="15" x2="12" y2="3"/>
                                    </svg>
                                    导出
                                </button>
                            </div>
                            <div class="export-item">
                                <div class="export-info">
                                    <div class="export-title">批量向量化</div>
                                    <div class="export-desc">将通过筛选的人才简历向量化存入向量库</div>
                                </div>
                                <button class="btn btn-secondary" id="batchVectorize">
                                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                                    </svg>
                                    执行
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 渲染统计数据
     */
    renderStatistics() {
        if (!this.statistics) {
            return '<div class="text-muted">暂无统计数据</div>';
        }

        const stats = this.statistics;
        const screeningStats = stats.by_screening_status || {};
        const workflowStats = stats.by_workflow_status || {};

        return `
            <div class="stats-overview">
                <div class="stat-item">
                    <div class="stat-number">${stats.total_talents || 0}</div>
                    <div class="stat-label">人才总数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">${stats.recent_7_days || 0}</div>
                    <div class="stat-label">近 7 天新增</div>
                </div>
            </div>

            <div class="stats-section">
                <h4 class="stats-title">筛选状态分布</h4>
                <div class="stats-bars">
                    ${this.renderStatBar('通过', screeningStats.qualified || 0, stats.total_talents, 'success')}
                    ${this.renderStatBar('未通过', screeningStats.unqualified || 0, stats.total_talents, 'danger')}
                </div>
            </div>

            <div class="stats-section">
                <h4 class="stats-title">工作流状态分布</h4>
                <div class="stats-list">
                    ${this.renderStatItem('已完成', workflowStats.completed || 0)}
                    ${this.renderStatItem('处理中', workflowStats.processing || 0)}
                    ${this.renderStatItem('待处理', workflowStats.pending || 0)}
                    ${this.renderStatItem('失败', workflowStats.failed || 0)}
                </div>
            </div>
        `;
    },

    /**
     * 渲染统计条
     */
    renderStatBar(label, value, total, type) {
        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
        return `
            <div class="stat-bar-item">
                <div class="stat-bar-header">
                    <span>${label}</span>
                    <span>${value} (${percentage}%)</span>
                </div>
                <div class="stat-bar">
                    <div class="stat-bar-fill ${type}" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    },

    /**
     * 渲染统计项
     */
    renderStatItem(label, value) {
        return `
            <div class="stats-list-item">
                <span>${label}</span>
                <span class="stats-list-value">${value}</span>
            </div>
        `;
    },

    /**
     * 初始化页面事件
     */
    initEvents() {
        // 查询按钮
        const queryBtn = document.getElementById('queryBtn');
        if (queryBtn) {
            queryBtn.addEventListener('click', () => this.executeQuery());
        }

        // 回车查询
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    this.executeQuery();
                }
            });
        }

        // 导出人才数据
        const exportTalents = document.getElementById('exportTalents');
        if (exportTalents) {
            exportTalents.addEventListener('click', () => this.exportTalentsData());
        }

        // 批量向量化
        const batchVectorize = document.getElementById('batchVectorize');
        if (batchVectorize) {
            batchVectorize.addEventListener('click', () => this.executeBatchVectorize());
        }
    },

    /**
     * 执行 RAG 查询
     */
    async executeQuery() {
        const queryInput = document.getElementById('queryInput');
        const topKSelect = document.getElementById('topKSelect');

        if (!queryInput) return;

        const query = queryInput.value.trim();
        if (!query) {
            UI.toast('请输入查询内容', 'warning');
            return;
        }

        const topK = parseInt(topKSelect?.value || '5');

        try {
            UI.showLoading();
            const response = await analysisApi.query(query, topK);

            if (response.success) {
                this.queryResults = response.data || [];
                this.showResults();
                UI.toast(`查询完成，找到 ${this.queryResults.length} 条结果`, 'success');
            }
        } catch (error) {
            console.error('查询失败:', error);
            UI.toast(error.message || '查询失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 显示查询结果
     */
    showResults() {
        const resultsCard = document.getElementById('resultsCard');
        const resultsBody = document.getElementById('resultsBody');
        const resultCount = document.getElementById('resultCount');

        if (!resultsCard || !resultsBody) return;

        resultsCard.style.display = 'block';

        if (resultCount) {
            resultCount.textContent = `共 ${this.queryResults.length} 条结果`;
        }

        if (this.queryResults.length === 0) {
            resultsBody.innerHTML = UI.renderEmpty('未找到相关结果', '请尝试修改查询条件');
            return;
        }

        resultsBody.innerHTML = this.queryResults.map((result, index) => `
            <div class="query-result">
                <div class="query-result-header">
                    <div class="query-result-name">
                        <span class="result-index">${index + 1}</span>
                        ${this.escapeHtml(result.metadata?.name || '未知')}
                    </div>
                    <div class="query-result-score">
                        相似度: ${result.distance ? (1 - result.distance).toFixed(3) : '-'}
                    </div>
                </div>
                <div class="query-result-meta">
                    ${result.metadata?.school ? `<span>${this.escapeHtml(result.metadata.school)}</span>` : ''}
                    ${result.metadata?.major ? `<span>${this.escapeHtml(result.metadata.major)}</span>` : ''}
                    ${result.metadata?.education_level ? `<span>${this.getEducationLabel(result.metadata.education_level)}</span>` : ''}
                    ${result.metadata?.work_years ? `<span>${result.metadata.work_years} 年经验</span>` : ''}
                </div>
                <div class="query-result-content">
                    ${this.escapeHtml(result.content || '')}
                </div>
            </div>
        `).join('');
    },

    /**
     * 导出人才数据
     */
    async exportTalentsData() {
        try {
            UI.showLoading();
            const response = await talentsApi.getList({ page: 1, page_size: 1000 });

            if (response.success) {
                const data = response.data.items || [];
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `talents_${new Date().toISOString().slice(0, 10)}.json`;
                a.click();
                URL.revokeObjectURL(url);
                UI.toast(`成功导出 ${data.length} 条人才数据`, 'success');
            }
        } catch (error) {
            console.error('导出失败:', error);
            UI.toast(error.message || '导出失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 执行批量向量化
     */
    async executeBatchVectorize() {
        UI.confirm('确定要执行批量向量化吗？这将把所有通过筛选的人才简历向量化存入向量库。', async () => {
            try {
                UI.showLoading();
                const response = await talentsApi.batchVectorize('qualified', 500);

                if (response.success) {
                    const data = response.data;
                    UI.toast(`向量化完成：成功 ${data.success} 条，失败 ${data.failed} 条`, 'success');
                }
            } catch (error) {
                console.error('批量向量化失败:', error);
                UI.toast(error.message || '批量向量化失败', 'error');
            } finally {
                UI.hideLoading();
            }
        });
    },

    /**
     * 获取学历标签
     */
    getEducationLabel(level) {
        const labels = {
            doctor: '博士',
            master: '硕士',
            bachelor: '本科',
            college: '大专',
            high_school: '高中及以下',
        };
        return labels[level] || level;
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
if (!document.getElementById('analysis-styles')) {
    const analysisStyles = document.createElement('style');
    analysisStyles.id = 'analysis-styles';
    analysisStyles.textContent = `
    .analysis-page .analysis-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .analysis-page .query-options {
        display: flex;
        align-items: flex-end;
        gap: 16px;
    }

    .analysis-page .query-options .form-group {
        margin-bottom: 0;
        min-width: 120px;
    }

    .analysis-page .query-options .btn {
        flex-shrink: 0;
    }

    .analysis-page .stats-overview {
        display: flex;
        gap: 24px;
        margin-bottom: 24px;
        padding-bottom: 24px;
        border-bottom: 1px solid var(--border-color);
    }

    .analysis-page .stat-item {
        text-align: center;
    }

    .analysis-page .stat-number {
        font-size: 32px;
        font-weight: 600;
        color: var(--primary-color);
        line-height: 1;
    }

    .analysis-page .stat-label {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 4px;
    }

    .analysis-page .stats-section {
        margin-bottom: 20px;
    }

    .analysis-page .stats-section:last-child {
        margin-bottom: 0;
    }

    .analysis-page .stats-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 12px;
    }

    .analysis-page .stats-bars {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .analysis-page .stat-bar-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .analysis-page .stat-bar-header {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
        color: var(--text-secondary);
    }

    .analysis-page .stat-bar {
        height: 8px;
        background-color: var(--bg-tertiary);
        border-radius: 4px;
        overflow: hidden;
    }

    .analysis-page .stat-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .analysis-page .stat-bar-fill.success {
        background-color: var(--success-color);
    }

    .analysis-page .stat-bar-fill.danger {
        background-color: var(--danger-color);
    }

    .analysis-page .stats-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .analysis-page .stats-list-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 12px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-sm);
        font-size: 13px;
    }

    .analysis-page .stats-list-value {
        font-weight: 600;
        color: var(--text-primary);
    }

    .analysis-page .result-count {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .analysis-page .query-result {
        padding: 16px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        margin-bottom: 12px;
    }

    .analysis-page .query-result:last-child {
        margin-bottom: 0;
    }

    .analysis-page .query-result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .analysis-page .query-result-name {
        font-weight: 600;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .analysis-page .result-index {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        background-color: var(--primary-color);
        color: #fff;
        border-radius: 50%;
        font-size: 12px;
        font-weight: 500;
    }

    .analysis-page .query-result-score {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .analysis-page .query-result-meta {
        display: flex;
        gap: 12px;
        font-size: 13px;
        color: var(--text-secondary);
        margin-bottom: 8px;
    }

    .analysis-page .query-result-meta span::after {
        content: '|';
        margin-left: 12px;
        color: var(--border-color);
    }

    .analysis-page .query-result-meta span:last-child::after {
        content: '';
        margin-left: 0;
    }

    .analysis-page .query-result-content {
        font-size: 14px;
        color: var(--text-secondary);
        line-height: 1.6;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .analysis-page .export-options {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .analysis-page .export-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
    }

    .analysis-page .export-title {
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .analysis-page .export-desc {
        font-size: 13px;
        color: var(--text-secondary);
    }

    @media (max-width: 1024px) {
        .analysis-page .analysis-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 768px) {
        .analysis-page .query-options {
            flex-direction: column;
            align-items: stretch;
        }

        .analysis-page .query-options .form-group {
            min-width: auto;
        }

        .analysis-page .stats-overview {
            flex-direction: column;
            gap: 16px;
        }
    }
`;
    document.head.appendChild(analysisStyles);
}

document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'analysis') {
        AnalysisPage.initEvents();
    }
});

window.AnalysisPage = AnalysisPage;
