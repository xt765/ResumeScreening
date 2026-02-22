/**
 * 人才信息查询模块
 * 提供搜索、表格展示、分页、详情查看功能
 */

const TalentsPage = {
    // 人才列表数据
    talents: [],
    // 分页信息
    pagination: {
        page: 1,
        pageSize: 10,
        total: 0,
        totalPages: 0,
    },
    // 筛选条件
    filters: {
        name: '',
        major: '',
        school: '',
        screening_status: '',
    },

    /**
     * 渲染页面
     */
    async render() {
        await this.loadTalents();
        return this.renderContent();
    },

    /**
     * 加载人才列表
     */
    async loadTalents() {
        try {
            const params = {
                page: this.pagination.page,
                page_size: this.pagination.pageSize,
            };

            // 添加筛选条件
            if (this.filters.name) params.name = this.filters.name;
            if (this.filters.major) params.major = this.filters.major;
            if (this.filters.school) params.school = this.filters.school;
            if (this.filters.screening_status) params.screening_status = this.filters.screening_status;

            const response = await talentsApi.getList(params);

            if (response.success) {
                this.talents = response.data.items || [];
                this.pagination.total = response.data.total || 0;
                this.pagination.totalPages = response.data.total_pages || 0;
            }
        } catch (error) {
            console.error('加载人才列表失败:', error);
            UI.toast('加载人才列表失败', 'error');
        }
    },

    /**
     * 渲染页面内容
     */
    renderContent() {
        return `
            <div class="talents-page">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">筛选条件</h3>
                    </div>
                    <div class="card-body">
                        <div class="filter-form">
                            <div class="filter-row">
                                <div class="filter-item">
                                    <label class="form-label">姓名</label>
                                    <input type="text" class="form-control" id="filterName" 
                                           placeholder="输入姓名" value="${this.filters.name}">
                                </div>
                                <div class="filter-item">
                                    <label class="form-label">专业</label>
                                    <input type="text" class="form-control" id="filterMajor" 
                                           placeholder="输入专业" value="${this.filters.major}">
                                </div>
                                <div class="filter-item">
                                    <label class="form-label">院校</label>
                                    <input type="text" class="form-control" id="filterSchool" 
                                           placeholder="输入院校" value="${this.filters.school}">
                                </div>
                                <div class="filter-item">
                                    <label class="form-label">筛选状态</label>
                                    <select class="form-control" id="filterStatus">
                                        <option value="">全部</option>
                                        <option value="qualified" ${this.filters.screening_status === 'qualified' ? 'selected' : ''}>通过</option>
                                        <option value="unqualified" ${this.filters.screening_status === 'unqualified' ? 'selected' : ''}>未通过</option>
                                    </select>
                                </div>
                            </div>
                            <div class="filter-actions">
                                <button class="btn btn-secondary" id="resetFilter">重置</button>
                                <button class="btn btn-primary" id="applyFilter">查询</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-3">
                    <div class="card-body" style="padding: 0;">
                        ${this.talents.length > 0 ? this.renderTable() : this.renderEmpty()}
                    </div>
                    ${this.talents.length > 0 ? `
                        <div class="card-footer">
                            ${UI.renderPagination(this.pagination.page, this.pagination.totalPages, (page) => this.changePage(page))}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    /**
     * 渲染表格
     */
    renderTable() {
        return `
            <div class="table-container">
                <table class="table">
                    <thead>
                        <tr>
                            <th>姓名</th>
                            <th>学历</th>
                            <th>院校</th>
                            <th>专业</th>
                            <th>工作年限</th>
                            <th>筛选状态</th>
                            <th>筛选日期</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.talents.map(talent => this.renderRow(talent)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * 渲染表格行
     */
    renderRow(talent) {
        const educationLabels = {
            doctor: '博士',
            master: '硕士',
            bachelor: '本科',
            college: '大专',
            high_school: '高中及以下',
        };

        const education = educationLabels[talent.education_level] || talent.education_level || '-';
        const statusBadge = talent.screening_status === 'qualified' 
            ? '<span class="badge badge-success">通过</span>'
            : '<span class="badge badge-danger">未通过</span>';

        return `
            <tr>
                <td>
                    <div class="talent-name">${this.escapeHtml(talent.name)}</div>
                </td>
                <td>${education}</td>
                <td>${this.escapeHtml(talent.school || '-')}</td>
                <td>${this.escapeHtml(talent.major || '-')}</td>
                <td>${talent.work_years || 0} 年</td>
                <td>${statusBadge}</td>
                <td>${UI.formatDateTime(talent.screening_date, false)}</td>
                <td>
                    <button class="btn btn-ghost btn-sm" onclick="TalentsPage.showDetail('${talent.id}')" title="查看详情">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                </td>
            </tr>
        `;
    },

    /**
     * 渲染空状态
     */
    renderEmpty() {
        return UI.renderEmpty(
            '暂无人才信息',
            '请先上传简历进行筛选',
            '上传简历',
            () => Router.navigateTo('upload')
        );
    },

    /**
     * 初始化页面事件
     */
    initEvents() {
        // 查询按钮
        const applyFilter = document.getElementById('applyFilter');
        if (applyFilter) {
            applyFilter.addEventListener('click', () => this.applyFilter());
        }

        // 重置按钮
        const resetFilter = document.getElementById('resetFilter');
        if (resetFilter) {
            resetFilter.addEventListener('click', () => this.resetFilter());
        }

        // 分页事件
        UI.bindPaginationEvents((page) => this.changePage(page));

        // 空状态按钮事件
        const emptyAction = document.getElementById('emptyAction');
        if (emptyAction) {
            emptyAction.addEventListener('click', () => Router.navigateTo('upload'));
        }

        // 回车搜索
        ['filterName', 'filterMajor', 'filterSchool'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        this.applyFilter();
                    }
                });
            }
        });
    },

    /**
     * 应用筛选条件
     */
    applyFilter() {
        this.filters.name = document.getElementById('filterName')?.value.trim() || '';
        this.filters.major = document.getElementById('filterMajor')?.value.trim() || '';
        this.filters.school = document.getElementById('filterSchool')?.value.trim() || '';
        this.filters.screening_status = document.getElementById('filterStatus')?.value || '';
        
        this.pagination.page = 1;
        this.refresh();
    },

    /**
     * 重置筛选条件
     */
    resetFilter() {
        this.filters = { name: '', major: '', school: '', screening_status: '' };
        this.pagination.page = 1;
        this.refresh();
    },

    /**
     * 切换页码
     */
    changePage(page) {
        this.pagination.page = page;
        this.refresh();
    },

    /**
     * 刷新页面
     */
    async refresh() {
        await this.loadTalents();
        const container = document.getElementById('pageContainer');
        if (container) {
            container.innerHTML = this.renderContent();
            this.initEvents();
        }
    },

    /**
     * 显示人才详情
     */
    async showDetail(id) {
        try {
            UI.showLoading();
            const response = await talentsApi.getDetail(id);

            if (response.success) {
                this.renderDetailModal(response.data);
            }
        } catch (error) {
            console.error('获取人才详情失败:', error);
            UI.toast('获取人才详情失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 渲染详情模态框
     */
    renderDetailModal(talent) {
        const educationLabels = {
            doctor: '博士',
            master: '硕士',
            bachelor: '本科',
            college: '大专',
            high_school: '高中及以下',
        };

        const education = educationLabels[talent.education_level] || talent.education_level || '-';
        const statusBadge = talent.screening_status === 'qualified' 
            ? '<span class="badge badge-success">通过</span>'
            : '<span class="badge badge-danger">未通过</span>';

        const content = `
            <div class="talent-detail">
                <div class="detail-header">
                    <div class="detail-avatar">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                            <circle cx="12" cy="7" r="4"/>
                        </svg>
                    </div>
                    <div class="detail-info">
                        <h3 class="detail-name">${this.escapeHtml(talent.name)}</h3>
                        <div class="detail-meta">
                            <span>${education}</span>
                            <span class="separator">|</span>
                            <span>${this.escapeHtml(talent.school || '-')}</span>
                            <span class="separator">|</span>
                            <span>${this.escapeHtml(talent.major || '-')}</span>
                        </div>
                    </div>
                    <div class="detail-status">${statusBadge}</div>
                </div>

                <div class="detail-section">
                    <h4 class="section-title">基本信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">联系电话</span>
                            <span class="detail-value">${this.escapeHtml(talent.phone || '-')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">电子邮箱</span>
                            <span class="detail-value">${this.escapeHtml(talent.email || '-')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">工作年限</span>
                            <span class="detail-value">${talent.work_years || 0} 年</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">毕业日期</span>
                            <span class="detail-value">${talent.graduation_date || '-'}</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4 class="section-title">技能标签</h4>
                    <div class="skill-tags">
                        ${(talent.skills || []).map(skill => `
                            <span class="skill-tag">${this.escapeHtml(skill)}</span>
                        `).join('') || '<span class="text-muted">暂无技能信息</span>'}
                    </div>
                </div>

                <div class="detail-section">
                    <h4 class="section-title">筛选信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">筛选状态</span>
                            <span class="detail-value">${statusBadge}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">筛选日期</span>
                            <span class="detail-value">${UI.formatDateTime(talent.screening_date, false)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">创建时间</span>
                            <span class="detail-value">${UI.formatDateTime(talent.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">更新时间</span>
                            <span class="detail-value">${UI.formatDateTime(talent.updated_at)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        UI.showModal('人才详情', content, '', 'lg');
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
const talentsStyles = document.createElement('style');
talentsStyles.textContent = `
    .talents-page .filter-form {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .talents-page .filter-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
    }

    .talents-page .filter-item {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .talents-page .filter-actions {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
    }

    .talent-name {
        font-weight: 500;
        color: var(--text-primary);
    }

    .talent-detail .detail-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 20px;
    }

    .talent-detail .detail-avatar {
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background-color: var(--bg-tertiary);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text-secondary);
    }

    .talent-detail .detail-info {
        flex: 1;
    }

    .talent-detail .detail-name {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
    }

    .talent-detail .detail-meta {
        color: var(--text-secondary);
        font-size: 14px;
    }

    .talent-detail .detail-meta .separator {
        margin: 0 8px;
        color: var(--border-color);
    }

    .talent-detail .detail-status {
        flex-shrink: 0;
    }

    .talent-detail .detail-section {
        margin-bottom: 24px;
    }

    .talent-detail .section-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-light);
    }

    .talent-detail .detail-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }

    .talent-detail .detail-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .talent-detail .detail-label {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .talent-detail .detail-value {
        font-weight: 500;
        color: var(--text-primary);
    }

    .talent-detail .skill-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .talent-detail .skill-tag {
        display: inline-block;
        padding: 4px 12px;
        background-color: var(--primary-bg);
        color: var(--primary-color);
        border-radius: 100px;
        font-size: 13px;
    }

    @media (max-width: 1024px) {
        .talents-page .filter-row {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 768px) {
        .talents-page .filter-row {
            grid-template-columns: 1fr;
        }

        .talent-detail .detail-grid {
            grid-template-columns: 1fr;
        }
    }
`;
document.head.appendChild(talentsStyles);

// 页面加载后初始化事件
document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'talents') {
        setTimeout(() => TalentsPage.initEvents(), 100);
    }
});

// 监听路由变化
window.addEventListener('hashchange', () => {
    if (AppState.currentPage === 'talents') {
        setTimeout(() => TalentsPage.initEvents(), 100);
    }
});

window.TalentsPage = TalentsPage;
