/**
 * 主应用模块
 * 提供路由、全局状态、UI 组件管理
 */

/**
 * 应用状态管理
 */
const AppState = {
    currentPage: 'dashboard',
    sidebarCollapsed: false,
    loading: false,
};

/**
 * 脚本动态加载器
 */
const ScriptLoader = {
    loadedScripts: new Set(),
    loadingScripts: new Map(),

    /**
     * 动态加载脚本
     * @param {string} src - 脚本路径
     * @returns {Promise<void>}
     */
    loadScript(src) {
        if (this.loadedScripts.has(src)) {
            return Promise.resolve();
        }

        if (this.loadingScripts.has(src)) {
            return this.loadingScripts.get(src);
        }

        const promise = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            
            script.onload = () => {
                this.loadedScripts.add(src);
                this.loadingScripts.delete(src);
                resolve();
            };
            
            script.onerror = () => {
                this.loadingScripts.delete(src);
                reject(new Error(`Failed to load script: ${src}`));
            };
            
            document.head.appendChild(script);
        });

        this.loadingScripts.set(src, promise);
        return promise;
    },

    /**
     * 批量加载脚本
     * @param {string[]} scripts - 脚本路径数组
     * @returns {Promise<void>}
     */
    async loadScripts(scripts) {
        if (!scripts || scripts.length === 0) return;
        await Promise.all(scripts.map(src => this.loadScript(src)));
    },
};

/**
 * 页面配置
 */
const PageConfig = {
    login: {
        title: '登录',
        subtitle: '请登录以继续使用系统',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>',
        render: () => LoginPage.render(),
        requireAuth: false,
        hideLayout: true,
        scripts: [],
    },
    dashboard: {
        title: '系统概览',
        subtitle: '查看系统整体运行状态和关键指标',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
        render: () => DashboardPage.render(),
        requireAuth: true,
        scripts: ['js/pages/dashboard.js'],
    },
    conditions: {
        title: '筛选条件',
        subtitle: '创建和管理简历筛选条件',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
        render: () => ConditionsPage.render(),
        requireAuth: true,
        scripts: ['js/pages/conditions.js'],
    },
    upload: {
        title: '简历上传',
        subtitle: '上传简历文件进行智能筛选',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
        render: () => UploadPage.render(),
        requireAuth: true,
        scripts: ['js/pages/upload.js'],
    },
    talents: {
        title: '人才信息',
        subtitle: '搜索和查看通过筛选的人才信息',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        render: () => TalentsPage.render(),
        requireAuth: true,
        scripts: ['js/pages/talents.js'],
    },
    analysis: {
        title: '数据分析',
        subtitle: 'RAG 智能查询和统计分析',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        render: () => AnalysisPage.render(),
        requireAuth: true,
        scripts: ['js/echarts.min.js', 'js/pages/analysis.js'],
    },
    monitor: {
        title: '系统监控',
        subtitle: '实时监控系统运行状态和日志信息',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>',
        render: () => MonitorPage.render(),
        requireAuth: true,
        scripts: ['js/echarts.min.js', 'js/pages/monitor.js'],
    },
    users: {
        title: '用户管理',
        subtitle: '管理系统用户账号',
        icon: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        render: () => UsersPage.render(),
        requireAuth: true,
        requireRole: 'admin',
        scripts: ['js/pages/users.js'],
    },
};

/**
 * 路由管理
 */
const Router = {
    /**
     * 初始化路由
     */
    init() {
        window.addEventListener('hashchange', () => this.handleRouteChange());
        this.handleRouteChange();
    },

    /**
     * 处理路由变化
     */
    handleRouteChange() {
        const hash = window.location.hash.slice(1) || '/dashboard';
        const fullPath = hash.replace('/', '') || 'dashboard';
        const [page, queryString] = fullPath.split('?');
        
        if (page === AppState.currentPage) {
            return;
        }

        const pageConfig = PageConfig[page];
        
        // 路由守卫：检查认证
        if (pageConfig?.requireAuth && !authApi.isLoggedIn()) {
            UI.toast('请先登录', 'warning');
            this.navigateTo('login');
            return;
        }
        
        // 角色权限检查
        if (pageConfig?.requireRole) {
            const user = getStoredUser();
            if (!user || user.role !== pageConfig.requireRole) {
                UI.toast('权限不足', 'error');
                this.navigateTo('dashboard');
                return;
            }
        }
        
        if (pageConfig?.hideLayout) {
            document.querySelector('.app-container').style.display = 'none';
            document.getElementById('loginContainer').style.display = 'block';
            document.body.classList.add('login-page');
        } else {
            document.querySelector('.app-container').style.display = 'flex';
            document.getElementById('loginContainer').style.display = 'none';
            document.body.classList.remove('login-page');
        }
        
        AppState.currentPage = page;
        
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === page) {
                item.classList.add('active');
            }
        });

        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle && pageConfig) {
            pageTitle.textContent = pageConfig.title;
        }
        
        const pageSubtitle = document.getElementById('pageSubtitle');
        if (pageSubtitle && pageConfig) {
            pageSubtitle.textContent = pageConfig.subtitle || '';
        }
        
        const pageIcon = document.getElementById('pageIcon');
        if (pageIcon && pageConfig && pageConfig.icon) {
            pageIcon.innerHTML = pageConfig.icon;
        }
        
        if (pageConfig) {
            this.renderPage(page);
        } else {
            this.renderPage('dashboard');
        }
    },

    navigateTo(page) {
        const targetHash = `/${page}`;
        
        if (window.location.hash === targetHash) {
            return;
        }
        
        window.location.hash = targetHash;
    },

    async renderPage(page) {
        const pageConfig = PageConfig[page];
        if (!pageConfig || !pageConfig.render) {
            console.error('页面配置不存在:', page);
            return;
        }

        const container = pageConfig.hideLayout 
            ? document.getElementById('loginContainer')
            : document.getElementById('pageContainer');
        
        if (!container) return;

        try {
            if (pageConfig.scripts && pageConfig.scripts.length > 0) {
                await ScriptLoader.loadScripts(pageConfig.scripts);
            }

            const pageModule = window[page.charAt(0).toUpperCase() + page.slice(1) + 'Page'];
            if (pageModule && typeof pageModule.clearCache === 'function') {
                pageModule.clearCache();
            }
            
            const content = await pageConfig.render();
            container.innerHTML = content;
            
            if (pageModule && typeof pageModule.initEvents === 'function') {
                pageModule.initEvents();
            }
        } catch (error) {
            console.error('页面渲染错误:', error);
            container.innerHTML = UI.renderError('页面加载失败，请刷新重试');
        }
    },
};

/**
 * UI 组件管理
 */
const UI = {
    /**
     * 显示加载遮罩
     */
    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('active');
        }
        AppState.loading = true;
    },

    /**
     * 隐藏加载遮罩
     */
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
        AppState.loading = false;
    },

    /**
     * 显示 Toast 提示
     * @param {string} message - 提示消息
     * @param {string} type - 类型: success, error, warning, info
     * @param {number} duration - 显示时长（毫秒）
     */
    toast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const icons = {
            success: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            info: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    /**
     * 显示模态框
     * @param {string} title - 标题
     * @param {string} content - 内容 HTML
     * @param {string} footer - 底部按钮 HTML
     * @param {string} size - 尺寸: '', 'lg', 'xl'
     */
    showModal(title, content, footer = '', size = '') {
        const overlay = document.getElementById('modalOverlay');
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        const modalFooter = document.getElementById('modalFooter');

        if (!overlay || !modal) return;

        modalTitle.textContent = title;
        modalBody.innerHTML = content;
        modalFooter.innerHTML = footer;

        modal.className = 'modal' + (size ? ` modal-${size}` : '');
        overlay.classList.add('active');
    },

    /**
     * 关闭模态框
     */
    closeModal() {
        const overlay = document.getElementById('modalOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    },

    /**
     * 确认对话框
     * @param {string} message - 确认消息
     * @param {Function} onConfirm - 确认回调
     * @param {Function} onCancel - 取消回调
     */
    confirm(message, onConfirm, onCancel = null) {
        const footer = `
            <button class="btn btn-secondary" id="confirmCancel">取消</button>
            <button class="btn btn-danger" id="confirmOk">确认</button>
        `;

        this.showModal('确认操作', `<p>${message}</p>`, footer);

        const confirmOk = document.getElementById('confirmOk');
        const confirmCancel = document.getElementById('confirmCancel');

        const handleConfirm = () => {
            this.closeModal();
            if (onConfirm) onConfirm();
            cleanup();
        };

        const handleCancel = () => {
            this.closeModal();
            if (onCancel) onCancel();
            cleanup();
        };

        const cleanup = () => {
            confirmOk.removeEventListener('click', handleConfirm);
            confirmCancel.removeEventListener('click', handleCancel);
        };

        confirmOk.addEventListener('click', handleConfirm);
        confirmCancel.addEventListener('click', handleCancel);
    },

    /**
     * 渲染空状态
     * @param {string} title - 标题
     * @param {string} description - 描述
     * @param {string} buttonText - 按钮文字
     * @param {Function} onClick - 点击回调
     */
    renderEmpty(title, description, buttonText = null, onClick = null) {
        return `
            <div class="empty-state">
                <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                <h3 class="empty-title">${title}</h3>
                <p class="empty-description">${description}</p>
                ${buttonText ? `<button class="btn btn-primary" id="emptyAction">${buttonText}</button>` : ''}
            </div>
        `;
    },

    /**
     * 渲染错误状态
     * @param {string} message - 错误消息
     */
    renderError(message) {
        return `
            <div class="empty-state">
                <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color: var(--danger-color)">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                <h3 class="empty-title">出错了</h3>
                <p class="empty-description">${message}</p>
                <button class="btn btn-primary" onclick="location.reload()">刷新页面</button>
            </div>
        `;
    },

    /**
     * 渲染分页组件
     * @param {number} current - 当前页
     * @param {number} total - 总页数
     * @param {Function} onChange - 页码变化回调
     */
    renderPagination(current, total, onChange) {
        if (total <= 1) return '';

        const pages = [];
        const showPages = 5;
        let start = Math.max(1, current - Math.floor(showPages / 2));
        let end = Math.min(total, start + showPages - 1);

        if (end - start + 1 < showPages) {
            start = Math.max(1, end - showPages + 1);
        }

        // 上一页
        pages.push(`
            <button class="pagination-btn" ${current === 1 ? 'disabled' : ''} data-page="${current - 1}">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 18 9 12 15 6"/>
                </svg>
            </button>
        `);

        // 第一页
        if (start > 1) {
            pages.push(`<button class="pagination-btn" data-page="1">1</button>`);
            if (start > 2) {
                pages.push(`<span class="pagination-info">...</span>`);
            }
        }

        // 页码
        for (let i = start; i <= end; i++) {
            pages.push(`
                <button class="pagination-btn ${i === current ? 'active' : ''}" data-page="${i}">${i}</button>
            `);
        }

        // 最后一页
        if (end < total) {
            if (end < total - 1) {
                pages.push(`<span class="pagination-info">...</span>`);
            }
            pages.push(`<button class="pagination-btn" data-page="${total}">${total}</button>`);
        }

        // 下一页
        pages.push(`
            <button class="pagination-btn" ${current === total ? 'disabled' : ''} data-page="${current + 1}">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                </svg>
            </button>
        `);

        return `
            <div class="pagination">
                ${pages.join('')}
                <span class="pagination-info">第 ${current} / ${total} 页</span>
            </div>
        `;
    },

    /**
     * 绑定分页事件
     * @param {Function} onChange - 页码变化回调
     */
    bindPaginationEvents(onChange) {
        document.querySelectorAll('.pagination-btn[data-page]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.currentTarget.dataset.page);
                if (!isNaN(page) && !e.currentTarget.disabled) {
                    onChange(page);
                }
            });
        });
    },

    /**
     * 格式化日期时间
     * @param {string|Date} date - 日期
     * @param {boolean} includeTime - 是否包含时间
     */
    formatDateTime(date, includeTime = true) {
        if (!date) return '-';
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        
        if (includeTime) {
            const hour = String(d.getHours()).padStart(2, '0');
            const minute = String(d.getMinutes()).padStart(2, '0');
            return `${year}-${month}-${day} ${hour}:${minute}`;
        }
        return `${year}-${month}-${day}`;
    },

    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
};

/**
 * 侧边栏管理
 */
const Sidebar = {
    /**
     * 初始化侧边栏
     */
    init() {
        const toggle = document.getElementById('menuToggle');
        const sidebar = document.querySelector('.sidebar');

        if (toggle && sidebar) {
            toggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }

        // 点击外部关闭侧边栏（移动端）
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024) {
                if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    },
};

/**
 * 模态框事件绑定
 */
const ModalEvents = {
    init() {
        const closeBtn = document.getElementById('modalClose');
        const overlay = document.getElementById('modalOverlay');

        if (closeBtn) {
            closeBtn.addEventListener('click', () => UI.closeModal());
        }

        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    UI.closeModal();
                }
            });
        }

        // ESC 键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                UI.closeModal();
            }
        });
    },
};

/**
 * 用户信息区域管理
 */
const UserArea = {
    /**
     * 初始化用户信息区域
     */
    init() {
        this.updateDisplay();
        this.bindEvents();
        
        // 监听登录/登出事件
        window.addEventListener('auth:login', () => this.updateDisplay());
        window.addEventListener('auth:logout', () => this.updateDisplay());
    },

    /**
     * 更新用户信息显示
     */
    updateDisplay() {
        const userInfoArea = document.getElementById('userInfoArea');
        const loginBtn = document.getElementById('loginBtn');
        const userName = document.getElementById('userName');
        const user = getStoredUser();

        if (user) {
            // 已登录状态
            if (userInfoArea) userInfoArea.style.display = 'flex';
            if (loginBtn) loginBtn.style.display = 'none';
            if (userName) userName.textContent = user.nickname || user.username;
            
            // 管理员显示用户管理菜单
            this.updateAdminMenu(user.role);
        } else {
            // 未登录状态
            if (userInfoArea) userInfoArea.style.display = 'none';
            if (loginBtn) loginBtn.style.display = 'inline-flex';
        }
    },

    /**
     * 更新管理员菜单
     */
    updateAdminMenu(role) {
        const existingUserNav = document.querySelector('.nav-item[data-page="users"]');
        
        if (role === 'admin' && !existingUserNav) {
            const nav = document.querySelector('.sidebar-nav');
            if (nav) {
                const userNavItem = document.createElement('a');
                userNavItem.href = '#/users';
                userNavItem.className = 'nav-item';
                userNavItem.dataset.page = 'users';
                userNavItem.innerHTML = `
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                    <span>用户管理</span>
                `;
                nav.appendChild(userNavItem);
                
                userNavItem.addEventListener('click', (e) => {
                    e.preventDefault();
                    Router.navigateTo('users');
                    if (window.innerWidth <= 1024) {
                        document.querySelector('.sidebar').classList.remove('open');
                    }
                });
            }
        } else if (role !== 'admin' && existingUserNav) {
            existingUserNav.remove();
        }
    },

    /**
     * 绑定事件
     */
    bindEvents() {
        const userInfoArea = document.getElementById('userInfoArea');
        const userDropdown = document.getElementById('userDropdown');
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const changePasswordBtn = document.getElementById('changePasswordBtn');

        // 点击用户区域显示/隐藏下拉菜单
        if (userInfoArea && userDropdown) {
            userInfoArea.addEventListener('click', (e) => {
                e.stopPropagation();
                userInfoArea.classList.toggle('active');
                userDropdown.classList.toggle('show');
            });

            // 点击外部关闭下拉菜单
            document.addEventListener('click', (e) => {
                if (!userInfoArea.contains(e.target)) {
                    userInfoArea.classList.remove('active');
                    userDropdown.classList.remove('show');
                }
            });
        }

        // 登录按钮
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                Router.navigateTo('login');
            });
        }

        // 登出按钮
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                await authApi.logout();
                UI.toast('已退出登录', 'info');
                Router.navigateTo('dashboard');
            });
        }

        // 修改密码按钮
        if (changePasswordBtn) {
            changePasswordBtn.addEventListener('click', () => {
                this.showChangePasswordModal();
            });
        }
    },

    /**
     * 显示修改密码模态框
     */
    showChangePasswordModal() {
        const content = `
            <div class="change-password-form">
                <div class="form-group">
                    <label class="form-label" for="oldPassword">当前密码</label>
                    <input type="password" id="oldPassword" class="form-input" placeholder="请输入当前密码" required>
                </div>
                <div class="form-group">
                    <label class="form-label" for="newPassword">新密码</label>
                    <input type="password" id="newPassword" class="form-input" placeholder="请输入新密码（至少6位）" required minlength="6">
                </div>
                <div class="form-group">
                    <label class="form-label" for="confirmPassword">确认新密码</label>
                    <input type="password" id="confirmPassword" class="form-input" placeholder="请再次输入新密码" required>
                </div>
                <div class="form-error" id="passwordError"></div>
            </div>
        `;

        const footer = `
            <button class="btn btn-secondary" id="cancelPasswordChange">取消</button>
            <button class="btn btn-primary" id="submitPasswordChange">确认修改</button>
        `;

        UI.showModal('修改密码', content, footer);

        setTimeout(() => {
            const submitBtn = document.getElementById('submitPasswordChange');
            const cancelBtn = document.getElementById('cancelPasswordChange');

            if (submitBtn) {
                submitBtn.addEventListener('click', async () => {
                    await this.handleChangePassword();
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
     * 处理修改密码
     */
    async handleChangePassword() {
        const oldPassword = document.getElementById('oldPassword')?.value;
        const newPassword = document.getElementById('newPassword')?.value;
        const confirmPassword = document.getElementById('confirmPassword')?.value;
        const errorDiv = document.getElementById('passwordError');

        if (!oldPassword || !newPassword || !confirmPassword) {
            if (errorDiv) {
                errorDiv.textContent = '请填写所有字段';
                errorDiv.style.display = 'block';
            }
            return;
        }

        if (newPassword !== confirmPassword) {
            if (errorDiv) {
                errorDiv.textContent = '两次输入的新密码不一致';
                errorDiv.style.display = 'block';
            }
            return;
        }

        if (newPassword.length < 6) {
            if (errorDiv) {
                errorDiv.textContent = '新密码长度至少为6位';
                errorDiv.style.display = 'block';
            }
            return;
        }

        try {
            const response = await authApi.changePassword(oldPassword, newPassword);
            if (response.success) {
                UI.toast('密码修改成功', 'success');
                UI.closeModal();
            } else {
                if (errorDiv) {
                    errorDiv.textContent = response.message || '密码修改失败';
                    errorDiv.style.display = 'block';
                }
            }
        } catch (error) {
            if (errorDiv) {
                errorDiv.textContent = error.message || '密码修改失败';
                errorDiv.style.display = 'block';
            }
        }
    },
};

/**
 * 应用初始化
 */
function initApp() {
    // 初始化用户信息区域
    UserArea.init();

    // 初始化侧边栏
    Sidebar.init();

    // 初始化模态框事件
    ModalEvents.init();

    // 初始化路由
    Router.init();

    // 绑定导航点击事件
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            if (page) {
                Router.navigateTo(page);
                // 移动端关闭侧边栏
                if (window.innerWidth <= 1024) {
                    document.querySelector('.sidebar').classList.remove('open');
                }
            }
        });
    });

    // 绑定刷新按钮事件
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            // 重新渲染当前页面
            Router.renderPage(AppState.currentPage);
            UI.toast('数据已刷新', 'success');
        });
    }

    console.log('简历智能筛选系统已初始化');
}

// DOM 加载完成后初始化应用
document.addEventListener('DOMContentLoaded', initApp);

// 导出全局对象
window.AppState = AppState;
window.Router = Router;
window.UI = UI;
window.UserArea = UserArea;
