/**
 * 人才信息查询模块
 * 提供搜索、表格展示、分页、详情查看功能
 */

const TalentsPage = {
    talents: [],
    pagination: {
        page: 1,
        pageSize: 10,
        total: 0,
        totalPages: 0,
    },
    filters: {
        name: '',
        major: '',
        school: '',
        screening_status: '',
        condition_id: '',
    },
    conditionList: [],
    selectedCondition: null,
    dataLoadedAt: null,
    CACHE_DURATION: 5 * 60 * 1000,

    async render() {
        this.loadDataAsync();
        return this.renderContent();
    },

    async loadDataAsync() {
        const now = Date.now();
        const cacheKey = JSON.stringify(this.filters) + this.pagination.page;
        
        if (this.talents.length > 0 && this.dataLoadedAt) {
            const age = now - this.dataLoadedAt;
            if (age < this.CACHE_DURATION) {
                return;
            }
        }

        try {
            await this.loadConditions();
            await this.loadTalents();
            this.dataLoadedAt = now;
            this.updateContent();
        } catch (error) {
            console.error('加载数据失败:', error);
        }
    },

    updateContent() {
        const container = document.getElementById('pageContainer');
        if (container) {
            container.innerHTML = this.renderContent();
            this.initEvents();
        }
    },

    clearCache() {
        this.dataLoadedAt = null;
    },

    /**
     * 加载筛选条件列表
     */
    async loadConditions() {
        try {
            const response = await conditionsApi.getList({ page_size: 100, is_active: true });
            if (response.success) {
                this.conditionList = response.data.items || [];
            }
        } catch (error) {
            console.error('加载筛选条件列表失败:', error);
        }
    },

    /**
     * 当选择筛选条件时更新详情
     */
    onConditionChange(conditionId) {
        if (conditionId) {
            this.selectedCondition = this.conditionList.find(c => c.id === conditionId);
        } else {
            this.selectedCondition = null;
        }
        this.renderConditionDetail();
    },

    /**
     * 渲染筛选条件详情
     */
    renderConditionDetail() {
        const container = document.getElementById('conditionDetail');
        if (!container) return;

        if (!this.selectedCondition) {
            container.innerHTML = '';
            return;
        }

        const config = this.selectedCondition.config || {};
        const educationLabels = {
            doctor: '博士',
            master: '硕士',
            bachelor: '本科',
            college: '大专',
            high_school: '高中及以下',
        };
        const schoolTierLabels = {
            top: '顶尖院校（985/C9）',
            key: '重点院校（211）',
            ordinary: '普通院校',
            overseas: '海外院校',
        };

        const details = [];
        if (config.education_level) {
            details.push(`<span class="condition-tag">学历: ${educationLabels[config.education_level] || config.education_level}</span>`);
        }
        if (config.experience_years !== undefined && config.experience_years !== null) {
            details.push(`<span class="condition-tag">工作年限: ${config.experience_years}+ 年</span>`);
        }
        if (config.school_tier) {
            details.push(`<span class="condition-tag">院校层次: ${schoolTierLabels[config.school_tier] || config.school_tier}</span>`);
        }
        if (config.skills && config.skills.length > 0) {
            details.push(`<span class="condition-tag">技能: ${config.skills.join(', ')}</span>`);
        }
        if (config.major && config.major.length > 0) {
            details.push(`<span class="condition-tag">专业: ${config.major.join(', ')}</span>`);
        }

        container.innerHTML = `
            <div class="condition-detail-box">
                <div class="condition-detail-header">
                    <span class="condition-name">${this.escapeHtml(this.selectedCondition.name)}</span>
                    <button class="btn btn-ghost btn-sm" onclick="TalentsPage.clearCondition()" title="清除筛选条件">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="condition-detail-tags">
                    ${details.join('')}
                </div>
            </div>
        `;
    },

    /**
     * 清除筛选条件
     */
    clearCondition() {
        this.filters.condition_id = '';
        this.selectedCondition = null;
        const select = document.getElementById('filterCondition');
        if (select) select.value = '';
        this.renderConditionDetail();
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
            if (this.filters.condition_id) params.condition_id = this.filters.condition_id;

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
                            <div class="filter-row">
                                <div class="filter-item">
                                    <label class="form-label">筛选条件</label>
                                    <select class="form-control" id="filterCondition" onchange="TalentsPage.onConditionChange(this.value)">
                                        <option value="">不限</option>
                                        ${this.conditionList.map(c => `
                                            <option value="${c.id}" ${this.filters.condition_id === c.id ? 'selected' : ''}>${this.escapeHtml(c.name)}</option>
                                        `).join('')}
                                    </select>
                                </div>
                                <div class="filter-item condition-detail-container" id="conditionDetail" colspan="3">
                                    ${this.selectedCondition ? this.renderConditionDetailStatic() : ''}
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
     * 静态渲染筛选条件详情（用于初始渲染）
     */
    renderConditionDetailStatic() {
        if (!this.selectedCondition) return '';
        
        const config = this.selectedCondition.config || {};
        const educationLabels = {
            doctor: '博士',
            master: '硕士',
            bachelor: '本科',
            college: '大专',
            high_school: '高中及以下',
        };
        const schoolTierLabels = {
            top: '顶尖院校（985/C9）',
            key: '重点院校（211）',
            ordinary: '普通院校',
            overseas: '海外院校',
        };

        const details = [];
        if (config.education_level) {
            details.push(`<span class="condition-tag">学历: ${educationLabels[config.education_level] || config.education_level}</span>`);
        }
        if (config.experience_years !== undefined && config.experience_years !== null) {
            details.push(`<span class="condition-tag">工作年限: ${config.experience_years}+ 年</span>`);
        }
        if (config.school_tier) {
            details.push(`<span class="condition-tag">院校层次: ${schoolTierLabels[config.school_tier] || config.school_tier}</span>`);
        }
        if (config.skills && config.skills.length > 0) {
            details.push(`<span class="condition-tag">技能: ${config.skills.join(', ')}</span>`);
        }
        if (config.major && config.major.length > 0) {
            details.push(`<span class="condition-tag">专业: ${config.major.join(', ')}</span>`);
        }

        return `
            <div class="condition-detail-box">
                <div class="condition-detail-header">
                    <span class="condition-name">${this.escapeHtml(this.selectedCondition.name)}</span>
                    <button class="btn btn-ghost btn-sm" onclick="TalentsPage.clearCondition()" title="清除筛选条件">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="condition-detail-tags">
                    ${details.join('')}
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
                    <div class="action-buttons">
                        <button class="btn btn-ghost btn-sm" onclick="TalentsPage.showDetail('${talent.id}')" title="查看详情">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                            </svg>
                        </button>
                        <button class="btn btn-ghost btn-sm btn-danger" onclick="TalentsPage.confirmDelete('${talent.id}', '${this.escapeHtml(talent.name)}')" title="删除">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                <line x1="10" y1="11" x2="10" y2="17"/>
                                <line x1="14" y1="11" x2="14" y2="17"/>
                            </svg>
                        </button>
                    </div>
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
        this.filters.condition_id = document.getElementById('filterCondition')?.value || '';
        
        this.pagination.page = 1;
        this.refresh();
    },

    /**
     * 重置筛选条件
     */
    resetFilter() {
        this.filters = { name: '', major: '', school: '', screening_status: '', condition_id: '' };
        this.selectedCondition = null;
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
        this.dataLoadedAt = null;
        await this.loadDataAsync();
    },

    /**
     * 确认删除
     */
    confirmDelete(id, name) {
        if (confirm(`确定要删除人才「${name}」吗？\n\n此操作可以恢复。`)) {
            this.deleteTalent(id);
        }
    },

    /**
     * 删除人才
     */
    async deleteTalent(id) {
        try {
            UI.showLoading();
            const response = await talentsApi.delete(id);

            if (response.success) {
                UI.toast('删除成功', 'success');
                await this.refresh();
            }
        } catch (error) {
            console.error('删除人才失败:', error);
            UI.toast('删除失败: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
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

        // 使用后端 API 地址获取头像
        const photoUrl = talent.id ? `http://localhost:8000/api/v1/talents/${talent.id}/photo` : '';
        const avatarContent = photoUrl 
            ? `<img src="${photoUrl}" alt="头像" class="avatar-image" onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
               <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" style="display:none;">
                   <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                   <circle cx="12" cy="7" r="4"/>
               </svg>`
            : `<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                   <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                   <circle cx="12" cy="7" r="4"/>
               </svg>`;

        const content = `
            <div class="talent-detail">
                <div class="detail-header">
                    <div class="detail-avatar">
                        ${avatarContent}
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
if (!document.getElementById('talents-styles')) {
    const talentsStyles = document.createElement('style');
    talentsStyles.id = 'talents-styles';
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

    .condition-detail-container {
        display: flex;
        align-items: center;
    }

    .condition-detail-box {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 12px 16px;
        background-color: var(--bg-secondary);
        border-radius: 8px;
        border: 1px solid var(--border-color);
        flex: 1;
    }

    .condition-detail-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .condition-detail-header .condition-name {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 14px;
    }

    .condition-detail-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .condition-tag {
        display: inline-block;
        padding: 4px 10px;
        background-color: var(--primary-bg);
        color: var(--primary-color);
        border-radius: 4px;
        font-size: 12px;
    }

    .action-buttons {
        display: flex;
        gap: 4px;
    }

    .action-buttons .btn-danger:hover {
        color: var(--danger-color);
        background-color: var(--danger-bg);
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
}

document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'talents') {
        TalentsPage.initEvents();
    }
});

window.TalentsPage = TalentsPage;
