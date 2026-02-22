/**
 * 用户管理页面模块
 * 提供管理员用户管理界面
 */

const UsersPage = {
    users: [],
    currentPage: 1,
    pageSize: 10,
    totalPages: 0,
    filters: {
        role: null,
        is_active: null,
        keyword: '',
    },

    /**
     * 渲染页面
     */
    async render() {
        await this.loadUsers();
        return this.renderContent();
    },

    /**
     * 渲染内容
     */
    renderContent() {
        return `
            <div class="users-page">
                <div class="page-toolbar">
                    <div class="toolbar-left">
                        <div class="search-box">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"/>
                                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                            </svg>
                            <input type="text" id="userSearch" placeholder="搜索用户名、邮箱、昵称..." value="${this.filters.keyword}">
                        </div>
                        <select class="form-select" id="roleFilter">
                            <option value="">全部角色</option>
                            <option value="admin" ${this.filters.role === 'admin' ? 'selected' : ''}>管理员</option>
                            <option value="hr" ${this.filters.role === 'hr' ? 'selected' : ''}>HR</option>
                            <option value="viewer" ${this.filters.role === 'viewer' ? 'selected' : ''}>访客</option>
                        </select>
                        <select class="form-select" id="statusFilter">
                            <option value="">全部状态</option>
                            <option value="true" ${this.filters.is_active === true ? 'selected' : ''}>已激活</option>
                            <option value="false" ${this.filters.is_active === false ? 'selected' : ''}>已禁用</option>
                        </select>
                    </div>
                    <div class="toolbar-right">
                        <button class="btn btn-primary" id="createUserBtn">
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="12" y1="5" x2="12" y2="19"/>
                                <line x1="5" y1="12" x2="19" y2="12"/>
                            </svg>
                            创建用户
                        </button>
                    </div>
                </div>
                
                <div class="card">
                    <div class="table-container">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>用户名</th>
                                    <th>昵称</th>
                                    <th>邮箱</th>
                                    <th>角色</th>
                                    <th>状态</th>
                                    <th>最后登录</th>
                                    <th>创建时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.renderUserRows()}
                            </tbody>
                        </table>
                    </div>
                    
                    ${this.renderPagination()}
                </div>
            </div>
        `;
    },

    /**
     * 渲染用户行
     */
    renderUserRows() {
        if (!this.users || this.users.length === 0) {
            return `
                <tr>
                    <td colspan="8">
                        ${UI.renderEmpty('暂无用户', '点击"创建用户"添加新用户')}
                    </td>
                </tr>
            `;
        }

        return this.users.map(user => `
            <tr>
                <td>
                    <div class="user-cell">
                        <div class="user-avatar-sm">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                <circle cx="12" cy="7" r="4"/>
                            </svg>
                        </div>
                        <span>${user.username}</span>
                    </div>
                </td>
                <td>${user.nickname || '-'}</td>
                <td>${user.email}</td>
                <td>
                    <span class="badge badge-${this.getRoleBadgeClass(user.role)}">${this.getRoleLabel(user.role)}</span>
                </td>
                <td>
                    <span class="badge badge-${user.is_active ? 'success' : 'danger'}">${user.is_active ? '已激活' : '已禁用'}</span>
                </td>
                <td>${user.last_login ? UI.formatDateTime(user.last_login) : '-'}</td>
                <td>${UI.formatDateTime(user.created_at, false)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-secondary" onclick="UsersPage.editUser('${user.id}')" title="编辑">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="UsersPage.resetPassword('${user.id}')" title="重置密码">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                        </button>
                        ${user.is_active 
                            ? `<button class="btn btn-sm btn-danger" onclick="UsersPage.disableUser('${user.id}')" title="禁用">
                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                                </svg>
                               </button>`
                            : `<button class="btn btn-sm btn-success" onclick="UsersPage.enableUser('${user.id}')" title="启用">
                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                    <polyline points="22 4 12 14.01 9 11.01"/>
                                </svg>
                               </button>`
                        }
                    </div>
                </td>
            </tr>
        `).join('');
    },

    /**
     * 渲染分页
     */
    renderPagination() {
        return UI.renderPagination(this.currentPage, this.totalPages, (page) => {
            this.currentPage = page;
            this.loadUsersAndRender();
        });
    },

    /**
     * 获取角色标签
     */
    getRoleLabel(role) {
        const labels = {
            admin: '管理员',
            hr: 'HR',
            viewer: '访客',
        };
        return labels[role] || role;
    },

    /**
     * 获取角色徽章样式
     */
    getRoleBadgeClass(role) {
        const classes = {
            admin: 'primary',
            hr: 'info',
            viewer: 'secondary',
        };
        return classes[role] || 'secondary';
    },

    /**
     * 加载用户列表
     */
    async loadUsers() {
        try {
            const params = {
                page: this.currentPage,
                page_size: this.pageSize,
            };

            if (this.filters.role) params.role = this.filters.role;
            if (this.filters.is_active !== null) params.is_active = this.filters.is_active;
            if (this.filters.keyword) params.keyword = this.filters.keyword;

            const response = await usersApi.getList(params);
            
            if (response.success && response.data) {
                this.users = response.data.items || [];
                this.totalPages = response.data.total_pages || 1;
            }
        } catch (error) {
            console.error('加载用户列表失败:', error);
            this.users = [];
        }
    },

    /**
     * 加载用户并重新渲染
     */
    async loadUsersAndRender() {
        await this.loadUsers();
        const container = document.getElementById('pageContainer');
        if (container) {
            container.innerHTML = this.renderContent();
            this.initEvents();
        }
    },

    /**
     * 初始化事件
     */
    initEvents() {
        const searchInput = document.getElementById('userSearch');
        const roleFilter = document.getElementById('roleFilter');
        const statusFilter = document.getElementById('statusFilter');
        const createUserBtn = document.getElementById('createUserBtn');

        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.filters.keyword = searchInput.value.trim();
                    this.currentPage = 1;
                    this.loadUsersAndRender();
                }
            });
        }

        if (roleFilter) {
            roleFilter.addEventListener('change', () => {
                this.filters.role = roleFilter.value || null;
                this.currentPage = 1;
                this.loadUsersAndRender();
            });
        }

        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                const value = statusFilter.value;
                this.filters.is_active = value === '' ? null : value === 'true';
                this.currentPage = 1;
                this.loadUsersAndRender();
            });
        }

        if (createUserBtn) {
            createUserBtn.addEventListener('click', () => {
                this.showCreateUserModal();
            });
        }

        UI.bindPaginationEvents((page) => {
            this.currentPage = page;
            this.loadUsersAndRender();
        });
    },

    /**
     * 显示创建用户模态框
     */
    showCreateUserModal() {
        const content = `
            <div class="create-user-form">
                <div class="form-group">
                    <label class="form-label" for="newUsername">用户名 *</label>
                    <input type="text" id="newUsername" class="form-input" placeholder="请输入用户名" required minlength="3" maxlength="50">
                </div>
                <div class="form-group">
                    <label class="form-label" for="newEmail">邮箱 *</label>
                    <input type="email" id="newEmail" class="form-input" placeholder="请输入邮箱" required>
                </div>
                <div class="form-group">
                    <label class="form-label" for="newPassword">初始密码 *</label>
                    <input type="password" id="newPassword" class="form-input" placeholder="请输入初始密码（至少6位）" required minlength="6">
                </div>
                <div class="form-group">
                    <label class="form-label" for="newNickname">昵称</label>
                    <input type="text" id="newNickname" class="form-input" placeholder="请输入昵称">
                </div>
                <div class="form-group">
                    <label class="form-label" for="newRole">角色 *</label>
                    <select id="newRole" class="form-select" required>
                        <option value="hr">HR</option>
                        <option value="viewer">访客</option>
                        <option value="admin">管理员</option>
                    </select>
                </div>
                <div class="form-error" id="createUserError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelCreateUser">取消</button>
            <button class="btn btn-primary" id="submitCreateUser">创建</button>
        `;

        UI.showModal('创建用户', content, footer);

        setTimeout(() => {
            const submitBtn = document.getElementById('submitCreateUser');
            const cancelBtn = document.getElementById('cancelCreateUser');

            if (submitBtn) {
                submitBtn.addEventListener('click', async () => {
                    await this.handleCreateUser();
                });
            }

            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    UI.closeModal();
                });
            }
        }, 100);
    },

    /**
     * 处理创建用户
     */
    async handleCreateUser() {
        const username = document.getElementById('newUsername')?.value?.trim();
        const email = document.getElementById('newEmail')?.value?.trim();
        const password = document.getElementById('newPassword')?.value;
        const nickname = document.getElementById('newNickname')?.value?.trim();
        const role = document.getElementById('newRole')?.value;
        const errorDiv = document.getElementById('createUserError');

        if (!username || !email || !password) {
            if (errorDiv) {
                errorDiv.textContent = '请填写必填字段';
                errorDiv.style.display = 'block';
            }
            return;
        }

        try {
            const response = await usersApi.create({
                username,
                email,
                password,
                nickname: nickname || '',
                role,
            });

            if (response.success) {
                UI.toast('用户创建成功', 'success');
                UI.closeModal();
                this.loadUsersAndRender();
            } else {
                if (errorDiv) {
                    errorDiv.textContent = response.message || '创建失败';
                    errorDiv.style.display = 'block';
                }
            }
        } catch (error) {
            if (errorDiv) {
                errorDiv.textContent = error.message || '创建失败';
                errorDiv.style.display = 'block';
            }
        }
    },

    /**
     * 编辑用户
     */
    editUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const content = `
            <div class="edit-user-form">
                <div class="form-group">
                    <label class="form-label" for="editNickname">昵称</label>
                    <input type="text" id="editNickname" class="form-input" value="${user.nickname || ''}" placeholder="请输入昵称">
                </div>
                <div class="form-group">
                    <label class="form-label" for="editEmail">邮箱</label>
                    <input type="email" id="editEmail" class="form-input" value="${user.email}" placeholder="请输入邮箱">
                </div>
                <div class="form-group">
                    <label class="form-label" for="editRole">角色</label>
                    <select id="editRole" class="form-select">
                        <option value="hr" ${user.role === 'hr' ? 'selected' : ''}>HR</option>
                        <option value="viewer" ${user.role === 'viewer' ? 'selected' : ''}>访客</option>
                        <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>管理员</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="editIsActive" ${user.is_active ? 'checked' : ''}>
                        账号激活
                    </label>
                </div>
                <div class="form-error" id="editUserError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelEditUser">取消</button>
            <button class="btn btn-primary" id="submitEditUser">保存</button>
        `;

        UI.showModal('编辑用户', content, footer);

        setTimeout(() => {
            const submitBtn = document.getElementById('submitEditUser');
            const cancelBtn = document.getElementById('cancelEditUser');

            if (submitBtn) {
                submitBtn.addEventListener('click', async () => {
                    await this.handleEditUser(userId);
                });
            }

            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    UI.closeModal();
                });
            }
        }, 100);
    },

    /**
     * 处理编辑用户
     */
    async handleEditUser(userId) {
        const nickname = document.getElementById('editNickname')?.value?.trim();
        const email = document.getElementById('editEmail')?.value?.trim();
        const role = document.getElementById('editRole')?.value;
        const isActive = document.getElementById('editIsActive')?.checked;
        const errorDiv = document.getElementById('editUserError');

        try {
            const response = await usersApi.update(userId, {
                nickname,
                email,
                role,
                is_active: isActive,
            });

            if (response.success) {
                UI.toast('用户信息已更新', 'success');
                UI.closeModal();
                this.loadUsersAndRender();
            } else {
                if (errorDiv) {
                    errorDiv.textContent = response.message || '更新失败';
                    errorDiv.style.display = 'block';
                }
            }
        } catch (error) {
            if (errorDiv) {
                errorDiv.textContent = error.message || '更新失败';
                errorDiv.style.display = 'block';
            }
        }
    },

    /**
     * 重置密码
     */
    resetPassword(userId) {
        const content = `
            <div class="reset-password-form">
                <p class="form-hint">为用户设置新密码</p>
                <div class="form-group">
                    <label class="form-label" for="resetNewPassword">新密码 *</label>
                    <input type="password" id="resetNewPassword" class="form-input" placeholder="请输入新密码（至少6位）" required minlength="6">
                </div>
                <div class="form-group">
                    <label class="form-label" for="resetConfirmPassword">确认密码 *</label>
                    <input type="password" id="resetConfirmPassword" class="form-input" placeholder="请再次输入新密码" required>
                </div>
                <div class="form-error" id="resetPasswordError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelResetPassword">取消</button>
            <button class="btn btn-primary" id="submitResetPassword">重置</button>
        `;

        UI.showModal('重置密码', content, footer);

        setTimeout(() => {
            const submitBtn = document.getElementById('submitResetPassword');
            const cancelBtn = document.getElementById('cancelResetPassword');

            if (submitBtn) {
                submitBtn.addEventListener('click', async () => {
                    await this.handleResetPassword(userId);
                });
            }

            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    UI.closeModal();
                });
            }
        }, 100);
    },

    /**
     * 处理重置密码
     */
    async handleResetPassword(userId) {
        const newPassword = document.getElementById('resetNewPassword')?.value;
        const confirmPassword = document.getElementById('resetConfirmPassword')?.value;
        const errorDiv = document.getElementById('resetPasswordError');

        if (!newPassword || !confirmPassword) {
            if (errorDiv) {
                errorDiv.textContent = '请填写所有字段';
                errorDiv.style.display = 'block';
            }
            return;
        }

        if (newPassword !== confirmPassword) {
            if (errorDiv) {
                errorDiv.textContent = '两次输入的密码不一致';
                errorDiv.style.display = 'block';
            }
            return;
        }

        if (newPassword.length < 6) {
            if (errorDiv) {
                errorDiv.textContent = '密码长度至少为6位';
                errorDiv.style.display = 'block';
            }
            return;
        }

        try {
            const response = await usersApi.resetPassword(userId, newPassword);
            if (response.success) {
                UI.toast('密码已重置', 'success');
                UI.closeModal();
            } else {
                if (errorDiv) {
                    errorDiv.textContent = response.message || '重置失败';
                    errorDiv.style.display = 'block';
                }
            }
        } catch (error) {
            if (errorDiv) {
                errorDiv.textContent = error.message || '重置失败';
                errorDiv.style.display = 'block';
            }
        }
    },

    /**
     * 禁用用户
     */
    disableUser(userId) {
        UI.confirm('确定要禁用该用户吗？禁用后用户将无法登录系统。', async () => {
            try {
                const response = await usersApi.delete(userId);
                if (response.success) {
                    UI.toast('用户已禁用', 'success');
                    this.loadUsersAndRender();
                } else {
                    UI.toast(response.message || '操作失败', 'error');
                }
            } catch (error) {
                UI.toast(error.message || '操作失败', 'error');
            }
        });
    },

    /**
     * 启用用户
     */
    async enableUser(userId) {
        try {
            const response = await usersApi.update(userId, { is_active: true });
            if (response.success) {
                UI.toast('用户已启用', 'success');
                this.loadUsersAndRender();
            } else {
                UI.toast(response.message || '操作失败', 'error');
            }
        } catch (error) {
            UI.toast(error.message || '操作失败', 'error');
        }
    },

    /**
     * 清除缓存
     */
    clearCache() {
        this.users = [];
    },
};

window.UsersPage = UsersPage;
