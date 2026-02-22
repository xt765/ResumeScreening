/**
 * 用户管理页面模块
 * 提供管理员用户管理界面
 */

const UsersPage = {
    users: [],
    currentPage: 1,
    pageSize: 10,
    totalPages: 0,
    totalUsers: 0,
    filters: {
        role: null,
        is_active: null,
        keyword: '',
    },
    // 系统管理员用户名
    SYSTEM_ADMIN_USERNAME: 'xt765',

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
                ${this.renderToolbar()}
                ${this.renderTable()}
                ${this.renderPagination()}
            </div>
        `;
    },

    /**
     * 渲染工具栏
     */
    renderToolbar() {
        return `
            <div class="users-toolbar">
                <div class="toolbar-section">
                    <div class="search-box">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                        <input type="text" id="userSearch" placeholder="搜索用户名、邮箱" value="${this.filters.keyword}">
                    </div>
                </div>
                <div class="toolbar-section">
                    <div class="filter-group">
                        <select class="form-select" id="roleFilter">
                            <option value="">全部角色</option>
                            <option value="admin" ${this.filters.role === 'admin' ? 'selected' : ''}>管理员</option>
                            <option value="hr" ${this.filters.role === 'hr' ? 'selected' : ''}>HR</option>
                        </select>
                        <select class="form-select" id="statusFilter">
                            <option value="">全部状态</option>
                            <option value="true" ${this.filters.is_active === true ? 'selected' : ''}>已激活</option>
                            <option value="false" ${this.filters.is_active === false ? 'selected' : ''}>已禁用</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" id="createUserBtn">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        创建用户
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * 渲染用户表格
     */
    renderTable() {
        if (!this.users || this.users.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-icon">
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                            <circle cx="9" cy="7" r="4"/>
                            <line x1="17" y1="11" x2="23" y2="11"/>
                        </svg>
                    </div>
                    <h3 class="empty-title">暂无用户</h3>
                    <p class="empty-description">点击"创建用户"按钮添加新用户</p>
                </div>
            `;
        }

        return `
            <div class="users-table-container">
                <table class="users-table">
                    <thead>
                        <tr>
                            <th>用户名</th>
                            <th>昵称</th>
                            <th>邮箱</th>
                            <th>角色</th>
                            <th>状态</th>
                            <th>最后登录</th>
                            <th>创建时间</th>
                            <th class="text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.users.map(user => this.renderTableRow(user)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * 渲染表格行
     */
    renderTableRow(user) {
        const isSystemAdmin = user.username === this.SYSTEM_ADMIN_USERNAME;
        const roleInfo = this.getRoleInfo(user.role);
        const statusInfo = user.is_active 
            ? { class: 'status-active', label: '已激活' }
            : { class: 'status-inactive', label: '已禁用' };

        return `
            <tr class="${isSystemAdmin ? 'system-admin-row' : ''} ${!user.is_active ? 'inactive-row' : ''}">
                <td>
                    <div class="user-info">
                        <div class="user-avatar ${isSystemAdmin ? 'admin-avatar' : ''}">
                            ${isSystemAdmin ? 'SA' : user.username.charAt(0).toUpperCase()}
                        </div>
                        <div class="user-details">
                            <div class="username">${user.username}</div>
                            ${isSystemAdmin ? '<div class="system-admin-badge">系统管理员</div>' : ''}
                        </div>
                    </div>
                </td>
                <td>${user.nickname || '-'}</td>
                <td>${user.email}</td>
                <td>
                    <span class="role-badge ${roleInfo.class}">
                        ${roleInfo.label}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${statusInfo.class}">
                        ${statusInfo.label}
                    </span>
                </td>
                <td>${user.last_login ? UI.formatDateTime(user.last_login) : '从未登录'}</td>
                <td>${UI.formatDateTime(user.created_at, false)}</td>
                <td class="text-right">
                    <div class="action-buttons">
                        <button class="action-btn" onclick="UsersPage.editUser('${user.id}')" title="编辑">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="action-btn" onclick="UsersPage.resetPassword('${user.id}')" title="重置密码">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                        </button>
                        ${this.renderStatusButton(user, isSystemAdmin)}
                        ${this.renderDeleteButton(user, isSystemAdmin)}
                    </div>
                </td>
            </tr>
        `;
    },

    /**
     * 渲染状态按钮
     */
    renderStatusButton(user, isSystemAdmin) {
        if (isSystemAdmin) {
            return `
                <button class="action-btn disabled" disabled title="系统管理员不能被禁用">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                    </svg>
                </button>
            `;
        }

        if (user.is_active) {
            return `
                <button class="action-btn danger" onclick="UsersPage.disableUser('${user.id}')" title="禁用用户">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                    </svg>
                </button>
            `;
        } else {
            return `
                <button class="action-btn success" onclick="UsersPage.enableUser('${user.id}')" title="启用用户">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </button>
            `;
        }
    },

    /**
     * 渲染删除按钮
     */
    renderDeleteButton(user, isSystemAdmin) {
        if (isSystemAdmin) {
            return `
                <button class="action-btn disabled" disabled title="系统管理员不能被删除">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            `;
        }

        return `
            <button class="action-btn danger" onclick="UsersPage.deleteUser('${user.id}')" title="删除用户">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
            </button>
        `;
    },

    /**
     * 获取角色信息
     */
    getRoleInfo(role) {
        const roles = {
            admin: { label: '管理员', class: 'role-admin' },
            hr: { label: 'HR', class: 'role-hr' }
        };
        return roles[role] || { label: role, class: 'role-default' };
    },

    /**
     * 渲染分页
     */
    renderPagination() {
        if (this.totalPages <= 1) return '';
        
        return `
            <div class="users-pagination">
                ${UI.renderPagination(this.currentPage, this.totalPages, (page) => {
                    this.currentPage = page;
                    this.loadUsersAndRender();
                })}
                <div class="pagination-info">
                    共 ${this.totalUsers} 条记录，每页 ${this.pageSize} 条
                </div>
            </div>
        `;
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
                this.totalUsers = response.data.total || 0;
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

        // 搜索框事件
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.filters.keyword = searchInput.value.trim();
                    this.currentPage = 1;
                    this.loadUsersAndRender();
                }
            });
            
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.filters.keyword = e.target.value.trim();
                    this.currentPage = 1;
                    this.loadUsersAndRender();
                }, 500);
            });
        }

        // 角色筛选
        if (roleFilter) {
            roleFilter.addEventListener('change', () => {
                this.filters.role = roleFilter.value || null;
                this.currentPage = 1;
                this.loadUsersAndRender();
            });
        }

        // 状态筛选
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                const value = statusFilter.value;
                this.filters.is_active = value === '' ? null : value === 'true';
                this.currentPage = 1;
                this.loadUsersAndRender();
            });
        }

        // 创建用户按钮
        if (createUserBtn) {
            createUserBtn.addEventListener('click', () => {
                this.showCreateUserModal();
            });
        }

        // 分页事件
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
            <div class="form-container">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label required">用户名</label>
                        <input type="text" id="newUsername" class="form-input" placeholder="请输入用户名" required minlength="3" maxlength="50">
                    </div>
                    <div class="form-group">
                        <label class="form-label">昵称</label>
                        <input type="text" id="newNickname" class="form-input" placeholder="请输入昵称（可选）">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label required">邮箱</label>
                        <input type="email" id="newEmail" class="form-input" placeholder="请输入邮箱地址" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label required">角色</label>
                        <select id="newRole" class="form-input" required>
                            <option value="hr">HR</option>
                            <option value="admin">管理员</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label required">初始密码</label>
                    <input type="password" id="newPassword" class="form-input" placeholder="请输入初始密码（至少6位）" required minlength="6">
                </div>
                <div class="form-error" id="createUserError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelCreateUser">取消</button>
            <button class="btn btn-primary" id="submitCreateUser">创建用户</button>
        `;

        UI.showModal('创建用户', content, footer, 'lg');

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

        if (!username || !email || !password || !role) {
            this.showError(errorDiv, '请填写所有必填字段');
            return;
        }

        if (username.length < 3) {
            this.showError(errorDiv, '用户名至少3个字符');
            return;
        }

        if (password.length < 6) {
            this.showError(errorDiv, '密码至少6个字符');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showError(errorDiv, '请输入有效的邮箱地址');
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
                this.showError(errorDiv, response.message || '创建失败');
            }
        } catch (error) {
            this.showError(errorDiv, error.message || '创建失败，请稍后重试');
        }
    },

    /**
     * 编辑用户
     */
    editUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const isSystemAdmin = user.username === this.SYSTEM_ADMIN_USERNAME;

        const content = `
            <div class="form-container">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">用户名</label>
                        <input type="text" class="form-input" value="${user.username}" disabled>
                    </div>
                    <div class="form-group">
                        <label class="form-label">昵称</label>
                        <input type="text" id="editNickname" class="form-input" value="${user.nickname || ''}" placeholder="请输入昵称">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label required">邮箱</label>
                        <input type="email" id="editEmail" class="form-input" value="${user.email}" placeholder="请输入邮箱">
                    </div>
                    <div class="form-group">
                        <label class="form-label required">角色</label>
                        <select id="editRole" class="form-input" ${isSystemAdmin ? 'disabled' : ''}>
                            <option value="hr" ${user.role === 'hr' ? 'selected' : ''}>HR</option>
                            <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>管理员</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-checkbox">
                        <input type="checkbox" id="editIsActive" ${user.is_active ? 'checked' : ''} ${isSystemAdmin ? 'disabled' : ''}>
                        <span class="checkbox-label">账号已激活</span>
                    </label>
                </div>
                ${isSystemAdmin ? '<div class="form-hint">系统管理员的角色和状态不可修改</div>' : ''}
                <div class="form-error" id="editUserError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelEditUser">取消</button>
            <button class="btn btn-primary" id="submitEditUser">保存修改</button>
        `;

        UI.showModal('编辑用户', content, footer, 'lg');

        setTimeout(() => {
            const submitBtn = document.getElementById('submitEditUser');
            const cancelBtn = document.getElementById('cancelEditUser');

            if (submitBtn) {
                submitBtn.addEventListener('click', async () => {
                    await this.handleEditUser(userId, isSystemAdmin);
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
    async handleEditUser(userId, isSystemAdmin) {
        const nickname = document.getElementById('editNickname')?.value?.trim();
        const email = document.getElementById('editEmail')?.value?.trim();
        const role = isSystemAdmin ? undefined : document.getElementById('editRole')?.value;
        const isActive = isSystemAdmin ? undefined : document.getElementById('editIsActive')?.checked;
        const errorDiv = document.getElementById('editUserError');

        if (!email) {
            this.showError(errorDiv, '请输入邮箱地址');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.showError(errorDiv, '请输入有效的邮箱地址');
            return;
        }

        try {
            const updateData = {
                nickname,
                email,
            };
            
            if (!isSystemAdmin) {
                updateData.role = role;
                updateData.is_active = isActive;
            }

            const response = await usersApi.update(userId, updateData);

            if (response.success) {
                UI.toast('用户信息已更新', 'success');
                UI.closeModal();
                
                // 检查是否是当前登录用户，如果是则更新右上角显示
                const currentUser = getStoredUser();
                if (currentUser && currentUser.id === userId) {
                    // 更新 localStorage 中的用户信息
                    currentUser.nickname = nickname;
                    currentUser.email = email;
                    if (!isSystemAdmin && role) {
                        currentUser.role = role;
                    }
                    setStoredUser(currentUser);
                    
                    // 更新右上角显示
                    if (window.UserArea && typeof window.UserArea.updateDisplay === 'function') {
                        window.UserArea.updateDisplay();
                    }
                }
                
                this.loadUsersAndRender();
            } else {
                this.showError(errorDiv, response.message || '更新失败');
            }
        } catch (error) {
            this.showError(errorDiv, error.message || '更新失败，请稍后重试');
        }
    },

    /**
     * 重置密码
     */
    resetPassword(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const content = `
            <div class="form-container">
                <div class="form-hint-box">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <span>为用户 <strong>${user.username}</strong> 设置新密码</span>
                </div>
                <div class="form-group">
                    <label class="form-label required">新密码</label>
                    <input type="password" id="resetNewPassword" class="form-input" placeholder="请输入新密码（至少6位）" required minlength="6">
                </div>
                <div class="form-group">
                    <label class="form-label required">确认密码</label>
                    <input type="password" id="resetConfirmPassword" class="form-input" placeholder="请再次输入新密码" required>
                </div>
                <div class="form-error" id="resetPasswordError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelResetPassword">取消</button>
            <button class="btn btn-primary" id="submitResetPassword">确认重置</button>
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
            this.showError(errorDiv, '请填写所有字段');
            return;
        }

        if (newPassword.length < 6) {
            this.showError(errorDiv, '密码至少6个字符');
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showError(errorDiv, '两次输入的密码不一致');
            return;
        }

        try {
            const response = await usersApi.resetPassword(userId, newPassword);
            if (response.success) {
                UI.toast('密码已重置成功', 'success');
                UI.closeModal();
            } else {
                this.showError(errorDiv, response.message || '重置失败');
            }
        } catch (error) {
            this.showError(errorDiv, error.message || '重置失败，请稍后重试');
        }
    },

    /**
     * 禁用用户
     */
    disableUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        if (user.username === this.SYSTEM_ADMIN_USERNAME) {
            UI.toast('系统管理员不能被禁用', 'error');
            return;
        }

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
     * 删除用户
     */
    deleteUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        if (user.username === this.SYSTEM_ADMIN_USERNAME) {
            UI.toast('系统管理员不能被删除', 'error');
            return;
        }

        UI.confirm('确定要永久删除该用户吗？此操作不可恢复！', async () => {
            try {
                const response = await usersApi.permanentDelete(userId);
                if (response.success) {
                    UI.toast('用户已删除', 'success');
                    this.loadUsersAndRender();
                } else {
                    UI.toast(response.message || '操作失败', 'error');
                }
            } catch (error) {
                UI.toast(error.message || '操作失败', 'error');
            }
        }, '删除');
    },

    /**
     * 显示错误信息
     */
    showError(errorDiv, message) {
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    },

    /**
     * 清除缓存
     */
    clearCache() {
        this.users = [];
        this.totalUsers = 0;
    },
};

window.UsersPage = UsersPage;