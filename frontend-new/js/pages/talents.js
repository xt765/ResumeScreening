/**
 * 人才信息查询模块
 * 提供搜索、表格展示、分页、详情查看、编辑、批量操作功能
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
        logic: 'and',
    },
    conditionList: [],
    selectedCondition: null,
    selectedIds: new Set(),
    dataLoadedAt: null,
    CACHE_DURATION: 5 * 60 * 1000,

    async render() {
        this.loadDataAsync();
        return this.renderContent();
    },

    async loadDataAsync() {
        const now = Date.now();
        
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

    onConditionChange(conditionId) {
        if (conditionId) {
            this.selectedCondition = this.conditionList.find(c => c.id === conditionId);
        } else {
            this.selectedCondition = null;
        }
        this.renderConditionDetail();
    },

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

    clearCondition() {
        this.filters.condition_id = '';
        this.selectedCondition = null;
        const select = document.getElementById('filterCondition');
        if (select) select.value = '';
        this.renderConditionDetail();
    },

    async loadTalents() {
        try {
            const params = {
                page: this.pagination.page,
                page_size: this.pagination.pageSize,
            };

            if (this.filters.name) params.name = this.filters.name;
            if (this.filters.major) params.major = this.filters.major;
            if (this.filters.school) params.school = this.filters.school;
            if (this.filters.screening_status) params.screening_status = this.filters.screening_status;
            if (this.filters.condition_id) params.condition_id = this.filters.condition_id;
            if (this.filters.logic) params.logic = this.filters.logic;

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

    renderContent() {
        return `
            <div class="talents-page">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">搜索筛选</h3>
                    </div>
                    <div class="card-body">
                        <div class="filter-form">
                            <div class="filter-row logic-row">
                                <div class="filter-item logic-item">
                                    <label class="form-label">条件逻辑</label>
                                    <select class="form-control" id="filterLogic">
                                        <option value="and" ${this.filters.logic === 'and' ? 'selected' : ''}>AND（所有条件都满足）</option>
                                        <option value="or" ${this.filters.logic === 'or' ? 'selected' : ''}>OR（任一条件满足）</option>
                                    </select>
                                </div>
                            </div>
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
                                    <label class="form-label">预设条件</label>
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

    renderTable() {
        const allSelected = this.talents.length > 0 && this.talents.every(t => this.selectedIds.has(t.id));
        
        return `
            ${this.selectedIds.size > 0 ? this.renderBatchToolbar() : ''}
            <div class="table-container">
                <table class="table">
                    <thead>
                        <tr>
                            <th class="checkbox-col">
                                <input type="checkbox" id="selectAll" ${allSelected ? 'checked' : ''} 
                                       onchange="TalentsPage.toggleSelectAll()">
                            </th>
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

    renderBatchToolbar() {
        return `
            <div class="batch-toolbar">
                <span class="batch-info">已选择 ${this.selectedIds.size} 项</span>
                <div class="batch-actions">
                    <button class="btn btn-sm btn-danger" onclick="TalentsPage.batchDelete()">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                        批量删除
                    </button>
                    <button class="btn btn-sm btn-success" onclick="TalentsPage.batchUpdateStatus('qualified')">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        批量标记通过
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="TalentsPage.batchUpdateStatus('unqualified')">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                        批量标记未通过
                    </button>
                </div>
            </div>
        `;
    },

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
        const isSelected = this.selectedIds.has(talent.id);
        const rowClass = isSelected ? 'selected' : '';

        return `
            <tr class="${rowClass}">
                <td class="checkbox-col">
                    <input type="checkbox" ${isSelected ? 'checked' : ''} 
                           onchange="TalentsPage.toggleSelect('${talent.id}')">
                </td>
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
                        <button class="btn btn-ghost btn-sm" onclick="TalentsPage.showEditModal('${talent.id}')" title="编辑">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
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

    renderEmpty() {
        return UI.renderEmpty(
            '暂无人才信息',
            '请先上传简历进行筛选',
            '上传简历',
            () => Router.navigateTo('upload')
        );
    },

    initEvents() {
        const applyFilter = document.getElementById('applyFilter');
        if (applyFilter) {
            applyFilter.addEventListener('click', () => this.applyFilter());
        }

        const resetFilter = document.getElementById('resetFilter');
        if (resetFilter) {
            resetFilter.addEventListener('click', () => this.resetFilter());
        }

        UI.bindPaginationEvents((page) => this.changePage(page));

        const emptyAction = document.getElementById('emptyAction');
        if (emptyAction) {
            emptyAction.addEventListener('click', () => Router.navigateTo('upload'));
        }

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

    toggleSelectAll() {
        const allSelected = this.talents.every(t => this.selectedIds.has(t.id));
        if (allSelected) {
            this.talents.forEach(t => this.selectedIds.delete(t.id));
        } else {
            this.talents.forEach(t => this.selectedIds.add(t.id));
        }
        this.updateContent();
    },

    toggleSelect(id) {
        if (this.selectedIds.has(id)) {
            this.selectedIds.delete(id);
        } else {
            this.selectedIds.add(id);
        }
        this.updateContent();
    },

    async batchDelete() {
        if (this.selectedIds.size === 0) {
            UI.toast('请先选择要删除的记录', 'warning');
            return;
        }

        if (!confirm(`确定要删除选中的 ${this.selectedIds.size} 条记录吗？\n\n此操作可以恢复。`)) {
            return;
        }

        try {
            UI.showLoading();
            const response = await talentsApi.batchDelete(Array.from(this.selectedIds));

            if (response.success) {
                UI.toast(response.message, 'success');
                this.selectedIds.clear();
                await this.refresh();
            }
        } catch (error) {
            console.error('批量删除失败:', error);
            UI.toast('批量删除失败: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    },

    async batchUpdateStatus(status) {
        if (this.selectedIds.size === 0) {
            UI.toast('请先选择要操作的记录', 'warning');
            return;
        }

        const statusText = status === 'qualified' ? '通过' : '未通过';
        if (!confirm(`确定要将选中的 ${this.selectedIds.size} 条记录标记为${statusText}吗？`)) {
            return;
        }

        try {
            UI.showLoading();
            const response = await talentsApi.batchUpdateStatus(Array.from(this.selectedIds), status);

            if (response.success) {
                UI.toast(response.message, 'success');
                this.selectedIds.clear();
                await this.refresh();
            }
        } catch (error) {
            console.error('批量更新状态失败:', error);
            UI.toast('批量更新状态失败: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    },

    applyFilter() {
        this.filters.name = document.getElementById('filterName')?.value.trim() || '';
        this.filters.major = document.getElementById('filterMajor')?.value.trim() || '';
        this.filters.school = document.getElementById('filterSchool')?.value.trim() || '';
        this.filters.screening_status = document.getElementById('filterStatus')?.value || '';
        this.filters.condition_id = document.getElementById('filterCondition')?.value || '';
        this.filters.logic = document.getElementById('filterLogic')?.value || 'and';
        
        this.pagination.page = 1;
        this.selectedIds.clear();
        this.refresh();
    },

    resetFilter() {
        this.filters = { name: '', major: '', school: '', screening_status: '', condition_id: '', logic: 'and' };
        this.selectedCondition = null;
        this.pagination.page = 1;
        this.selectedIds.clear();
        this.refresh();
    },

    changePage(page) {
        this.pagination.page = page;
        this.refresh();
    },

    async refresh() {
        this.dataLoadedAt = null;
        await this.loadDataAsync();
    },

    confirmDelete(id, name) {
        if (confirm(`确定要删除人才「${name}」吗？\n\n此操作可以恢复。`)) {
            this.deleteTalent(id);
        }
    },

    async deleteTalent(id) {
        try {
            UI.showLoading();
            const response = await talentsApi.delete(id);

            if (response.success) {
                UI.toast('删除成功', 'success');
                this.selectedIds.delete(id);
                await this.refresh();
            }
        } catch (error) {
            console.error('删除人才失败:', error);
            UI.toast('删除失败: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    },

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

    async showEditModal(id) {
        try {
            UI.showLoading();
            const response = await talentsApi.getDetail(id);

            if (response.success) {
                this.renderEditModal(response.data);
            }
        } catch (error) {
            console.error('获取人才详情失败:', error);
            UI.toast('获取人才详情失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

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

    renderEditModal(talent) {
        const educationOptions = [
            { value: 'doctor', label: '博士' },
            { value: 'master', label: '硕士' },
            { value: 'bachelor', label: '本科' },
            { value: 'college', label: '大专' },
            { value: 'high_school', label: '高中及以下' },
        ];

        const educationLevel = talent.education_level || '';
        const selectedEducation = educationOptions.find(opt => 
            opt.value === educationLevel || opt.label === educationLevel
        )?.value || 'bachelor';

        const content = `
            <div class="talent-edit-form">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">姓名</label>
                        <input type="text" class="form-control" id="editName" value="${this.escapeHtml(talent.name || '')}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">学历</label>
                        <select class="form-control" id="editEducation">
                            ${educationOptions.map(opt => `
                                <option value="${opt.value}" ${selectedEducation === opt.value ? 'selected' : ''}>${opt.label}</option>
                            `).join('')}
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">院校</label>
                        <input type="text" class="form-control" id="editSchool" value="${this.escapeHtml(talent.school || '')}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">专业</label>
                        <input type="text" class="form-control" id="editMajor" value="${this.escapeHtml(talent.major || '')}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">工作年限</label>
                        <input type="number" class="form-control" id="editWorkYears" value="${talent.work_years || 0}" min="0" max="50">
                    </div>
                    <div class="form-group">
                        <label class="form-label">毕业日期</label>
                        <input type="date" class="form-control" id="editGraduationDate" value="${talent.graduation_date || ''}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">联系电话</label>
                        <input type="text" class="form-control" id="editPhone" value="${this.escapeHtml(talent.phone || '')}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">电子邮箱</label>
                        <input type="email" class="form-control" id="editEmail" value="${this.escapeHtml(talent.email || '')}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">筛选状态</label>
                        <select class="form-control" id="editScreeningStatus">
                            <option value="qualified" ${talent.screening_status === 'qualified' ? 'selected' : ''}>通过</option>
                            <option value="unqualified" ${talent.screening_status === 'unqualified' ? 'selected' : ''}>未通过</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">技能标签</label>
                    <div class="skills-input-container">
                        <div class="skills-tags-container" id="skillsTagsContainer">
                            ${(talent.skills || []).map(skill => `
                                <span class="skill-tag-edit" data-skill="${this.escapeHtml(skill)}">
                                    ${this.escapeHtml(skill)}
                                    <button type="button" class="skill-remove" onclick="TalentsPage.removeSkill('${this.escapeHtml(skill)}')">×</button>
                                </span>
                            `).join('')}
                        </div>
                        <div class="skill-input-row">
                            <input type="text" class="form-control skill-input" id="newSkillInput" placeholder="输入技能名称">
                            <button type="button" class="btn btn-sm btn-secondary" onclick="TalentsPage.addSkill()">添加</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" onclick="UI.closeModal()">取消</button>
            <button class="btn btn-primary" onclick="TalentsPage.saveEdit('${talent.id}')">保存</button>
        `;

        UI.showModal('编辑人才信息', content, footer, 'lg');
        
        this.currentEditSkills = [...(talent.skills || [])];

        const newSkillInput = document.getElementById('newSkillInput');
        if (newSkillInput) {
            newSkillInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addSkill();
                }
            });
        }
    },

    currentEditSkills: [],

    addSkill() {
        const input = document.getElementById('newSkillInput');
        const skill = input?.value.trim();
        
        if (!skill) return;
        if (this.currentEditSkills.includes(skill)) {
            UI.toast('该技能已存在', 'warning');
            return;
        }

        this.currentEditSkills.push(skill);
        this.updateSkillsTags();
        input.value = '';
    },

    removeSkill(skill) {
        this.currentEditSkills = this.currentEditSkills.filter(s => s !== skill);
        this.updateSkillsTags();
    },

    updateSkillsTags() {
        const container = document.getElementById('skillsTagsContainer');
        if (!container) return;

        container.innerHTML = this.currentEditSkills.map(skill => `
            <span class="skill-tag-edit" data-skill="${this.escapeHtml(skill)}">
                ${this.escapeHtml(skill)}
                <button type="button" class="skill-remove" onclick="TalentsPage.removeSkill('${this.escapeHtml(skill)}')">×</button>
            </span>
        `).join('');
    },

    async saveEdit(id) {
        const data = {
            name: document.getElementById('editName')?.value.trim() || null,
            education_level: document.getElementById('editEducation')?.value || null,
            school: document.getElementById('editSchool')?.value.trim() || null,
            major: document.getElementById('editMajor')?.value.trim() || null,
            work_years: parseInt(document.getElementById('editWorkYears')?.value) || null,
            graduation_date: document.getElementById('editGraduationDate')?.value || null,
            phone: document.getElementById('editPhone')?.value.trim() || null,
            email: document.getElementById('editEmail')?.value.trim() || null,
            screening_status: document.getElementById('editScreeningStatus')?.value || null,
            skills: this.currentEditSkills.length > 0 ? this.currentEditSkills : null,
        };

        Object.keys(data).forEach(key => {
            if (data[key] === null || data[key] === '') {
                delete data[key];
            }
        });

        try {
            UI.showLoading();
            const response = await talentsApi.update(id, data);

            if (response.success) {
                UI.toast('保存成功', 'success');
                UI.closeModal();
                await this.refresh();
            }
        } catch (error) {
            console.error('保存失败:', error);
            UI.toast('保存失败: ' + error.message, 'error');
        } finally {
            UI.hideLoading();
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

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

    .talents-page .filter-row.logic-row {
        grid-template-columns: 1fr;
    }

    .talents-page .filter-item.logic-item {
        max-width: 300px;
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

    .checkbox-col {
        width: 40px;
        text-align: center;
    }

    .checkbox-col input[type="checkbox"] {
        width: 16px;
        height: 16px;
        cursor: pointer;
    }

    .table tbody tr.selected {
        background-color: var(--primary-bg);
    }

    .batch-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background-color: var(--bg-secondary);
        border-bottom: 1px solid var(--border-color);
    }

    .batch-info {
        font-weight: 500;
        color: var(--primary-color);
    }

    .batch-actions {
        display: flex;
        gap: 8px;
    }

    .batch-actions .btn-sm {
        display: flex;
        align-items: center;
        gap: 4px;
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

    .talent-edit-form .form-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 16px;
    }

    .talent-edit-form .form-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .skills-input-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .skills-tags-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        min-height: 32px;
    }

    .skill-tag-edit {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        background-color: var(--primary-bg);
        color: var(--primary-color);
        border-radius: 4px;
        font-size: 13px;
    }

    .skill-remove {
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 16px;
        line-height: 1;
        padding: 0 2px;
    }

    .skill-remove:hover {
        color: var(--danger-color);
    }

    .skill-input-row {
        display: flex;
        gap: 8px;
    }

    .skill-input-row .skill-input {
        flex: 1;
    }

    @media (max-width: 1024px) {
        .talents-page .filter-row {
            grid-template-columns: repeat(2, 1fr);
        }

        .talent-edit-form .form-row {
            grid-template-columns: 1fr;
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
