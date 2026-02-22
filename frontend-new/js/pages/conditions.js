/**
 * 筛选条件管理模块
 * 提供条件列表、新增、编辑、删除功能
 */

const ConditionsPage = {
    // 条件列表数据
    conditions: [],
    // 分页信息
    pagination: {
        page: 1,
        pageSize: 10,
        total: 0,
        totalPages: 0,
    },
    // 搜索关键词
    searchKeyword: '',

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
            const response = await conditionsApi.getList({
                name: this.searchKeyword || undefined,
                page: this.pagination.page,
                page_size: this.pagination.pageSize,
            });

            if (response.success) {
                this.conditions = response.data.items || [];
                this.pagination.total = response.data.total || 0;
                this.pagination.totalPages = response.data.total_pages || 0;
            }
        } catch (error) {
            console.error('加载筛选条件失败:', error);
            UI.toast('加载筛选条件失败', 'error');
        }
    },

    /**
     * 渲染页面内容
     */
    renderContent() {
        return `
            <div class="conditions-page">
                <div class="page-toolbar">
                    <div class="search-box">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                        <input type="text" id="searchInput" placeholder="搜索条件名称..." value="${this.searchKeyword}">
                    </div>
                    <button class="btn btn-primary" id="createBtn">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        新增条件
                    </button>
                </div>

                <div class="card">
                    <div class="card-body" style="padding: 0;">
                        ${this.conditions.length > 0 ? this.renderTable() : this.renderEmpty()}
                    </div>
                    ${this.conditions.length > 0 ? `
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
                            <th>条件名称</th>
                            <th>描述</th>
                            <th>学历要求</th>
                            <th>工作年限</th>
                            <th>状态</th>
                            <th>创建时间</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.conditions.map(condition => this.renderRow(condition)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * 渲染表格行
     */
    renderRow(condition) {
        const educationLabels = {
            doctor: '博士',
            master: '硕士',
            bachelor: '本科',
            college: '大专',
            high_school: '高中及以下',
        };

        const config = condition.config || {};
        const education = config.education_level ? educationLabels[config.education_level] : '不限';
        const experience = config.experience_years ? `${config.experience_years}+ 年` : '不限';

        return `
            <tr>
                <td>
                    <div class="condition-name">${this.escapeHtml(condition.name)}</div>
                </td>
                <td>
                    <div class="condition-desc">${this.escapeHtml(condition.description || '-')}</div>
                </td>
                <td>${education}</td>
                <td>${experience}</td>
                <td>
                    <span class="badge ${condition.is_active ? 'badge-success' : 'badge-gray'}">
                        ${condition.is_active ? '启用' : '禁用'}
                    </span>
                </td>
                <td>${UI.formatDateTime(condition.created_at, false)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-ghost btn-sm" onclick="ConditionsPage.editCondition('${condition.id}')" title="编辑">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="btn btn-ghost btn-sm text-danger" onclick="ConditionsPage.deleteCondition('${condition.id}')" title="删除">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
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
            '暂无筛选条件',
            '点击上方"新增条件"按钮创建筛选条件',
            '新增条件',
            () => this.showCreateModal()
        );
    },

    /**
     * 初始化页面事件
     */
    initEvents() {
        // 搜索事件
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.searchKeyword = e.target.value.trim();
                    this.pagination.page = 1;
                    this.refresh();
                }, 300);
            });
        }

        // 新增按钮事件
        const createBtn = document.getElementById('createBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateModal());
        }

        // 分页事件
        UI.bindPaginationEvents((page) => this.changePage(page));

        // 空状态按钮事件
        const emptyAction = document.getElementById('emptyAction');
        if (emptyAction) {
            emptyAction.addEventListener('click', () => this.showCreateModal());
        }
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
        await this.loadConditions();
        const container = document.getElementById('pageContainer');
        if (container) {
            container.innerHTML = this.renderContent();
            this.initEvents();
        }
    },

    /**
     * 显示创建模态框
     */
    showCreateModal() {
        const content = this.renderConditionForm();
        const footer = `
            <button class="btn btn-secondary" onclick="UI.closeModal()">取消</button>
            <button class="btn btn-primary" id="submitCondition">保存</button>
        `;

        UI.showModal('新增筛选条件', content, footer, 'lg');

        // 绑定提交事件
        setTimeout(() => {
            const submitBtn = document.getElementById('submitCondition');
            if (submitBtn) {
                submitBtn.addEventListener('click', () => this.submitCreate());
            }
            this.initTagsInput();
        }, 100);
    },

    /**
     * 编辑筛选条件
     */
    async editCondition(id) {
        const condition = this.conditions.find(c => c.id === id);
        if (!condition) {
            UI.toast('条件不存在', 'error');
            return;
        }

        const content = this.renderConditionForm(condition);
        const footer = `
            <button class="btn btn-secondary" onclick="UI.closeModal()">取消</button>
            <button class="btn btn-primary" id="submitCondition">保存</button>
        `;

        UI.showModal('编辑筛选条件', content, footer, 'lg');

        // 绑定提交事件
        setTimeout(() => {
            const submitBtn = document.getElementById('submitCondition');
            if (submitBtn) {
                submitBtn.addEventListener('click', () => this.submitUpdate(id));
            }
            this.initTagsInput();
        }, 100);
    },

    /**
     * 渲染条件表单
     */
    renderConditionForm(condition = null) {
        const config = condition?.config || {};
        const skills = config.skills || [];
        const major = config.major || [];

        return `
            <form id="conditionForm">
                <div class="form-group">
                    <label class="form-label required">条件名称</label>
                    <input type="text" class="form-control" id="conditionName" 
                           value="${condition ? this.escapeHtml(condition.name) : ''}" 
                           placeholder="请输入条件名称" required>
                </div>

                <div class="form-group">
                    <label class="form-label">条件描述</label>
                    <textarea class="form-control" id="conditionDesc" rows="2" 
                              placeholder="请输入条件描述">${condition ? this.escapeHtml(condition.description || '') : ''}</textarea>
                </div>

                <div class="condition-config">
                    <div class="form-group">
                        <label class="form-label">学历要求</label>
                        <select class="form-control" id="educationLevel">
                            <option value="">不限</option>
                            <option value="doctor" ${config.education_level === 'doctor' ? 'selected' : ''}>博士</option>
                            <option value="master" ${config.education_level === 'master' ? 'selected' : ''}>硕士</option>
                            <option value="bachelor" ${config.education_level === 'bachelor' ? 'selected' : ''}>本科</option>
                            <option value="college" ${config.education_level === 'college' ? 'selected' : ''}>大专</option>
                            <option value="high_school" ${config.education_level === 'high_school' ? 'selected' : ''}>高中及以下</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">工作年限要求</label>
                        <input type="number" class="form-control" id="experienceYears" 
                               value="${config.experience_years || ''}" 
                               min="0" max="50" placeholder="最低年限，如：3">
                        <div class="form-hint">填写最低工作年限要求</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">学校层次</label>
                        <select class="form-control" id="schoolTier">
                            <option value="">不限</option>
                            <option value="top" ${config.school_tier === 'top' ? 'selected' : ''}>顶尖院校（985/C9）</option>
                            <option value="key" ${config.school_tier === 'key' ? 'selected' : ''}>重点院校（211）</option>
                            <option value="ordinary" ${config.school_tier === 'ordinary' ? 'selected' : ''}>普通院校</option>
                            <option value="overseas" ${config.school_tier === 'overseas' ? 'selected' : ''}>海外院校</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">启用状态</label>
                        <select class="form-control" id="isActive">
                            <option value="true" ${condition?.is_active !== false ? 'selected' : ''}>启用</option>
                            <option value="false" ${condition?.is_active === false ? 'selected' : ''}>禁用</option>
                        </select>
                    </div>

                    <div class="form-group full-width">
                        <label class="form-label">技能要求</label>
                        <div class="tags-input" id="skillsInput">
                            ${skills.map(skill => `
                                <span class="tag">
                                    ${this.escapeHtml(skill)}
                                    <span class="tag-remove" onclick="ConditionsPage.removeTag(this, 'skillsInput')">&times;</span>
                                </span>
                            `).join('')}
                            <input type="text" placeholder="输入技能后按回车添加" data-field="skills">
                        </div>
                        <div class="form-hint">输入技能名称后按回车键添加</div>
                    </div>

                    <div class="form-group full-width">
                        <label class="form-label">专业要求</label>
                        <div class="tags-input" id="majorInput">
                            ${major.map(m => `
                                <span class="tag">
                                    ${this.escapeHtml(m)}
                                    <span class="tag-remove" onclick="ConditionsPage.removeTag(this, 'majorInput')">&times;</span>
                                </span>
                            `).join('')}
                            <input type="text" placeholder="输入专业后按回车添加" data-field="major">
                        </div>
                        <div class="form-hint">输入专业名称后按回车键添加</div>
                    </div>
                </div>
            </form>
        `;
    },

    /**
     * 初始化标签输入
     */
    initTagsInput() {
        document.querySelectorAll('.tags-input input').forEach(input => {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const value = input.value.trim();
                    if (value) {
                        const container = input.parentElement;
                        const tag = document.createElement('span');
                        tag.className = 'tag';
                        tag.innerHTML = `
                            ${this.escapeHtml(value)}
                            <span class="tag-remove" onclick="ConditionsPage.removeTag(this)">&times;</span>
                        `;
                        container.insertBefore(tag, input);
                        input.value = '';
                    }
                }
            });
        });
    },

    /**
     * 移除标签
     */
    removeTag(element, containerId = null) {
        element.parentElement.remove();
    },

    /**
     * 获取表单数据
     */
    getFormData() {
        const name = document.getElementById('conditionName')?.value.trim();
        const description = document.getElementById('conditionDesc')?.value.trim();
        const educationLevel = document.getElementById('educationLevel')?.value;
        const experienceYears = document.getElementById('experienceYears')?.value;
        const schoolTier = document.getElementById('schoolTier')?.value;
        const isActive = document.getElementById('isActive')?.value === 'true';

        // 获取技能标签
        const skills = [];
        document.querySelectorAll('#skillsInput .tag').forEach(tag => {
            skills.push(tag.textContent.replace('×', '').trim());
        });

        // 获取专业标签
        const major = [];
        document.querySelectorAll('#majorInput .tag').forEach(tag => {
            major.push(tag.textContent.replace('×', '').trim());
        });

        if (!name) {
            UI.toast('请输入条件名称', 'warning');
            return null;
        }

        return {
            name,
            description: description || undefined,
            is_active: isActive,
            config: {
                skills,
                education_level: educationLevel || undefined,
                experience_years: experienceYears ? parseInt(experienceYears) : undefined,
                major,
                school_tier: schoolTier || undefined,
            },
        };
    },

    /**
     * 提交创建
     */
    async submitCreate() {
        const data = this.getFormData();
        if (!data) return;

        try {
            UI.showLoading();
            const response = await conditionsApi.create(data);
            
            if (response.success) {
                UI.toast('筛选条件创建成功', 'success');
                UI.closeModal();
                this.refresh();
            }
        } catch (error) {
            console.error('创建筛选条件失败:', error);
            UI.toast(error.message || '创建失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 提交更新
     */
    async submitUpdate(id) {
        const data = this.getFormData();
        if (!data) return;

        try {
            UI.showLoading();
            const response = await conditionsApi.update(id, data);
            
            if (response.success) {
                UI.toast('筛选条件更新成功', 'success');
                UI.closeModal();
                this.refresh();
            }
        } catch (error) {
            console.error('更新筛选条件失败:', error);
            UI.toast(error.message || '更新失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 删除筛选条件
     */
    deleteCondition(id) {
        UI.confirm('确定要删除该筛选条件吗？此操作不可恢复。', async () => {
            try {
                UI.showLoading();
                const response = await conditionsApi.delete(id);
                
                if (response.success) {
                    UI.toast('筛选条件删除成功', 'success');
                    this.refresh();
                }
            } catch (error) {
                console.error('删除筛选条件失败:', error);
                UI.toast(error.message || '删除失败', 'error');
            } finally {
                UI.hideLoading();
            }
        });
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
const conditionsStyles = document.createElement('style');
conditionsStyles.textContent = `
    .conditions-page .page-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        gap: 16px;
    }

    .condition-name {
        font-weight: 500;
        color: var(--text-primary);
    }

    .condition-desc {
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--text-secondary);
    }

    .action-buttons {
        display: flex;
        gap: 4px;
    }

    @media (max-width: 768px) {
        .conditions-page .page-toolbar {
            flex-direction: column;
            align-items: stretch;
        }

        .conditions-page .search-box {
            max-width: none;
        }
    }
`;
document.head.appendChild(conditionsStyles);

// 页面加载后初始化事件
document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'conditions') {
        setTimeout(() => ConditionsPage.initEvents(), 100);
    }
});

// 监听路由变化
window.addEventListener('hashchange', () => {
    if (AppState.currentPage === 'conditions') {
        setTimeout(() => ConditionsPage.initEvents(), 100);
    }
});

window.ConditionsPage = ConditionsPage;
