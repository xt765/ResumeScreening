/**
 * 首页模块
 * 提供系统概览、统计卡片、快捷操作
 */

const DashboardPage = {
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
                this.updateStats();
                return;
            }
        }

        try {
            const response = await analysisApi.getStatistics();
            this.statistics = response.data;
            this.dataLoadedAt = now;
            this.updateStats();
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    updateStats() {
        const statsContainer = document.querySelector('.stats-grid');
        if (statsContainer && this.statistics) {
            statsContainer.outerHTML = this.renderStats();
        }
    },

    renderContent() {
        return `
            <div class="dashboard-page">
                ${this.renderStats()}
                <div class="dashboard-grid">
                    ${this.renderQuickActions()}
                    ${this.renderRecentTalents()}
                </div>
            </div>
        `;
    },

    /**
     * 渲染统计卡片
     */
    renderStats() {
        const stats = this.statistics || {};
        const total = stats.total_talents || 0;
        const qualified = stats.by_screening_status?.qualified || 0;
        const unqualified = stats.by_screening_status?.unqualified || 0;
        const pending = stats.by_workflow_status?.pending || 0;
        const recent = stats.recent_7_days || 0;

        return `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon primary">
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                            <circle cx="9" cy="7" r="4"/>
                            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">人才总数</div>
                        <div class="stat-value">${total}</div>
                        <div class="stat-change positive">近 7 天新增 ${recent} 人</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon success">
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">通过筛选</div>
                        <div class="stat-value">${qualified}</div>
                        <div class="stat-change">${total > 0 ? ((qualified / total) * 100).toFixed(1) : 0}% 通过率</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon danger">
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">未通过筛选</div>
                        <div class="stat-value">${unqualified}</div>
                        <div class="stat-change">${total > 0 ? ((unqualified / total) * 100).toFixed(1) : 0}% 未通过率</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon warning">
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">处理中</div>
                        <div class="stat-value">${pending}</div>
                        <div class="stat-change">等待处理完成</div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 渲染快捷操作
     */
    renderQuickActions() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">快捷操作</h3>
                </div>
                <div class="card-body">
                    <div class="quick-actions">
                        <a href="#/upload" class="quick-action-item">
                            <div class="quick-action-icon primary">
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                    <polyline points="17 8 12 3 7 8"/>
                                    <line x1="12" y1="3" x2="12" y2="15"/>
                                </svg>
                            </div>
                            <div class="quick-action-content">
                                <div class="quick-action-title">上传简历</div>
                                <div class="quick-action-desc">上传简历文件进行智能筛选</div>
                            </div>
                        </a>

                        <a href="#/conditions" class="quick-action-item">
                            <div class="quick-action-icon success">
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 3v18M3 12h18M5.5 5.5l13 13M18.5 5.5l-13 13"/>
                                </svg>
                            </div>
                            <div class="quick-action-content">
                                <div class="quick-action-title">管理条件</div>
                                <div class="quick-action-desc">创建和管理筛选条件</div>
                            </div>
                        </a>

                        <a href="#/talents" class="quick-action-item">
                            <div class="quick-action-icon warning">
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="8"/>
                                    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                                </svg>
                            </div>
                            <div class="quick-action-content">
                                <div class="quick-action-title">查询人才</div>
                                <div class="quick-action-desc">搜索和查看人才信息</div>
                            </div>
                        </a>

                        <a href="#/analysis" class="quick-action-item">
                            <div class="quick-action-icon info">
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="20" x2="18" y2="10"/>
                                    <line x1="12" y1="20" x2="12" y2="4"/>
                                    <line x1="6" y1="20" x2="6" y2="14"/>
                                </svg>
                            </div>
                            <div class="quick-action-content">
                                <div class="quick-action-title">数据分析</div>
                                <div class="quick-action-desc">RAG 智能查询和统计分析</div>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 渲染最近人才列表
     */
    renderRecentTalents() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">系统状态</h3>
                </div>
                <div class="card-body">
                    <div class="system-info" id="systemInfo">
                        <div class="info-item">
                            <span class="info-label">后端服务</span>
                            <span class="info-value">
                                <span class="status-indicator loading" id="apiStatus"></span>
                                <span id="apiStatusText">检测中...</span>
                            </span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">API 地址</span>
                            <span class="info-value">http://localhost:8000</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">API 文档</span>
                            <span class="info-value">
                                <a href="http://localhost:8000/docs" target="_blank" class="link">查看文档</a>
                            </span>
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
        this.checkSystemHealth();
    },

    /**
     * 检查系统健康状态
     */
    async checkSystemHealth() {
        const statusEl = document.getElementById('apiStatus');
        const statusTextEl = document.getElementById('apiStatusText');

        if (!statusEl || !statusTextEl) return;

        try {
            const health = await healthApi.check();
            const allHealthy = health.status === 'healthy';

            statusEl.className = 'status-indicator ' + (allHealthy ? 'healthy' : 'degraded');
            statusTextEl.textContent = allHealthy ? '运行正常' : '部分服务异常';

            // 显示详细服务状态
            if (health.services) {
                const servicesHtml = Object.entries(health.services)
                    .map(([name, status]) => {
                        const isHealthy = status.status === 'healthy';
                        return `
                            <div class="service-status">
                                <span class="status-indicator ${isHealthy ? 'healthy' : 'unhealthy'}"></span>
                                <span>${this.getServiceName(name)}</span>
                            </div>
                        `;
                    })
                    .join('');

                const systemInfo = document.getElementById('systemInfo');
                const existingServices = document.getElementById('servicesStatus');
                if (existingServices) {
                    existingServices.innerHTML = servicesHtml;
                } else if (systemInfo) {
                    systemInfo.innerHTML += `
                        <div class="info-item" id="servicesStatus">
                            <span class="info-label">服务状态</span>
                            <div class="services-list">${servicesHtml}</div>
                        </div>
                    `;
                }
            }
        } catch (error) {
            statusEl.className = 'status-indicator unhealthy';
            statusTextEl.textContent = '连接失败';
        }
    },

    /**
     * 获取服务名称
     */
    getServiceName(name) {
        const names = {
            mysql: 'MySQL',
            redis: 'Redis',
            minio: 'MinIO',
            chromadb: 'ChromaDB',
        };
        return names[name] || name;
    },
};

// 添加页面特定样式
if (!document.getElementById('dashboard-styles')) {
    const dashboardStyles = document.createElement('style');
    dashboardStyles.id = 'dashboard-styles';
    dashboardStyles.textContent = `
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .quick-actions {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }

    .quick-action-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background-color: var(--bg-secondary);
        border-radius: var(--radius-md);
        text-decoration: none;
        transition: all var(--transition-fast);
    }

    .quick-action-item:hover {
        background-color: var(--bg-tertiary);
        transform: translateY(-2px);
    }

    .quick-action-icon {
        width: 48px;
        height: 48px;
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .quick-action-icon.primary {
        background-color: var(--primary-bg);
        color: var(--primary-color);
    }

    .quick-action-icon.success {
        background-color: var(--success-bg);
        color: var(--success-color);
    }

    .quick-action-icon.warning {
        background-color: var(--warning-bg);
        color: var(--warning-color);
    }

    .quick-action-icon.info {
        background-color: var(--info-bg);
        color: var(--info-color);
    }

    .quick-action-title {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .quick-action-desc {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .system-info {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .info-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid var(--border-color);
    }

    .info-item:last-child {
        border-bottom: none;
    }

    .info-label {
        font-weight: 500;
        color: var(--text-secondary);
    }

    .info-value {
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .link {
        color: var(--primary-color);
        text-decoration: none;
    }

    .link:hover {
        text-decoration: underline;
    }

    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .status-indicator.healthy {
        background-color: var(--success-color);
    }

    .status-indicator.unhealthy {
        background-color: var(--danger-color);
    }

    .status-indicator.degraded {
        background-color: var(--warning-color);
    }

    .status-indicator.loading {
        background-color: var(--text-muted);
        animation: pulse 1s infinite;
    }

    .services-list {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }

    .service-status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
    }

    @media (max-width: 1024px) {
        .dashboard-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 768px) {
        .quick-actions {
            grid-template-columns: 1fr;
        }
    }
`;
    document.head.appendChild(dashboardStyles);
}

document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'dashboard') {
        DashboardPage.initEvents();
    }
});

window.DashboardPage = DashboardPage;
