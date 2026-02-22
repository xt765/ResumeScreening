/**
 * 登录页面模块
 * 提供用户登录界面
 */

const LoginPage = {
    /**
     * 渲染登录页面
     */
    render() {
        return `
            <div class="login-container">
                <div class="login-card">
                    <div class="login-header">
                        <div class="login-logo">
                            <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                                <polyline points="14 2 14 8 20 8"/>
                                <path d="M9.5 11.5h5M9.5 14.5h5M9.5 17.5h3" stroke="currentColor" stroke-width="1.5" fill="none"/>
                            </svg>
                        </div>
                        <h1 class="login-title">简历智能筛选系统</h1>
                        <p class="login-subtitle">请登录以继续使用系统</p>
                    </div>
                    
                    <form class="login-form" id="loginForm">
                        <div class="form-group">
                            <label class="form-label" for="username">用户名</label>
                            <div class="input-wrapper">
                                <svg class="input-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                    <circle cx="12" cy="7" r="4"/>
                                </svg>
                                <input 
                                    type="text" 
                                    id="username" 
                                    name="username" 
                                    class="form-input" 
                                    placeholder="请输入用户名"
                                    autocomplete="username"
                                    required
                                >
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label" for="password">密码</label>
                            <div class="input-wrapper">
                                <svg class="input-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                                </svg>
                                <input 
                                    type="password" 
                                    id="password" 
                                    name="password" 
                                    class="form-input" 
                                    placeholder="请输入密码"
                                    autocomplete="current-password"
                                    required
                                >
                                <button type="button" class="password-toggle" id="passwordToggle">
                                    <svg class="eye-open" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                        <circle cx="12" cy="12" r="3"/>
                                    </svg>
                                    <svg class="eye-closed" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" style="display: none;">
                                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                                        <line x1="1" y1="1" x2="23" y2="23"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        
                        <div class="form-error" id="formError"></div>
                        
                        <button type="submit" class="btn btn-primary btn-block" id="loginBtn">
                            <span class="btn-text">登录</span>
                            <span class="btn-loading" style="display: none;">
                                <svg class="spinner" viewBox="0 0 24 24" width="20" height="20">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
                                </svg>
                                登录中...
                            </span>
                        </button>
                    </form>
                    
                    <div class="login-footer">
                        <p>© 2026 简历智能筛选系统</p>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 初始化事件
     */
    initEvents() {
        const form = document.getElementById('loginForm');
        const passwordToggle = document.getElementById('passwordToggle');
        const passwordInput = document.getElementById('password');

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleLogin();
            });
        }

        if (passwordToggle && passwordInput) {
            const eyeOpen = passwordToggle.querySelector('.eye-open');
            const eyeClosed = passwordToggle.querySelector('.eye-closed');
            
            passwordToggle.addEventListener('click', () => {
                const isPassword = passwordInput.type === 'password';
                passwordInput.type = isPassword ? 'text' : 'password';
                passwordToggle.classList.toggle('active');
                
                if (eyeOpen && eyeClosed) {
                    eyeOpen.style.display = isPassword ? 'none' : 'block';
                    eyeClosed.style.display = isPassword ? 'block' : 'none';
                }
            });
        }
    },

    /**
     * 处理登录
     */
    async handleLogin() {
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        const loginBtn = document.getElementById('loginBtn');
        const errorDiv = document.getElementById('formError');

        const username = usernameInput?.value?.trim();
        const password = passwordInput?.value;

        if (!username || !password) {
            this.showError('请输入用户名和密码');
                return;
            }

        this.setLoading(true);
        this.showError('');

        try {
            const response = await authApi.login(username, password);

            if (response.success) {
                UI.toast('登录成功', 'success');
                
                if (response.data?.is_first_login) {
                    this.showChangePasswordModal();
                } else {
                    window.location.hash = '/dashboard';
                }
            } else {
                this.showError(response.message || '登录失败');
            }
        } catch (error) {
            this.showError(error.message || '登录失败，请稍后重试');
        } finally {
            this.setLoading(false);
        }
    },

    /**
     * 显示错误信息
     */
    showError(message) {
        const errorDiv = document.getElementById('formError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = message ? 'block' : 'none';
        }
    },

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        const loginBtn = document.getElementById('loginBtn');
        const btnText = loginBtn?.querySelector('.btn-text');
        const btnLoading = loginBtn?.querySelector('.btn-loading');

        if (loginBtn) {
            loginBtn.disabled = loading;
        }
        if (btnText) {
            btnText.style.display = loading ? 'none' : 'inline';
        }
        if (btnLoading) {
            btnLoading.style.display = loading ? 'inline-flex' : 'none';
        }
    },

    /**
     * 显示修改密码模态框（首次登录）
     */
    showChangePasswordModal() {
        const content = `
            <div class="change-password-form">
                <p class="form-hint">首次登录需要修改密码</p>
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
            <button class="btn btn-secondary" id="skipPasswordChange">稍后修改</button>
            <button class="btn btn-primary" id="submitPasswordChange">确认修改</button>
        `;

        UI.showModal('修改密码', content, footer);

        setTimeout(() => {
            const submitBtn = document.getElementById('submitPasswordChange');
            const skipBtn = document.getElementById('skipPasswordChange');

            if (submitBtn) {
                submitBtn.addEventListener('click', async () => {
                    await this.handleChangePassword();
                });
            }

            if (skipBtn) {
                skipBtn.addEventListener('click', () => {
                    UI.closeModal();
                    window.location.hash = '/dashboard';
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
                window.location.hash = '/dashboard';
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

    /**
     * 清除缓存
     */
    clearCache() {
        // 登录页面无需缓存
    },
};

window.LoginPage = LoginPage;
