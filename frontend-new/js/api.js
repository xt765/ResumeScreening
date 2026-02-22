/**
 * API 封装模块
 * 提供与后端 FastAPI 的通信接口
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * 获取存储的 Token
 */
function getStoredToken() {
    return localStorage.getItem('token');
}

/**
 * 设置存储的 Token
 */
function setStoredToken(token) {
    if (token) {
        localStorage.setItem('token', token);
    } else {
        localStorage.removeItem('token');
    }
}

/**
 * 获取存储的用户信息
 */
function getStoredUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

/**
 * 设置存储的用户信息
 */
function setStoredUser(user) {
    if (user) {
        localStorage.setItem('user', JSON.stringify(user));
    } else {
        localStorage.removeItem('user');
    }
}

/**
 * 清除认证信息
 */
function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

/**
 * API 请求封装类
 */
class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    /**
     * 发送 HTTP 请求
     * @param {string} endpoint - API 端点
     * @param {Object} options - 请求选项
     * @returns {Promise<Object>} 响应数据
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = getStoredToken();
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        // 添加 Authorization 头
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        // 如果有 body 且是对象，转换为 JSON
        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        // FormData 不需要设置 Content-Type
        if (config.body instanceof FormData) {
            delete config.headers['Content-Type'];
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                // 401 错误清除认证信息
                if (response.status === 401) {
                    clearAuth();
                    window.dispatchEvent(new CustomEvent('auth:logout'));
                }
                throw new ApiError(data.detail || data.message || '请求失败', response.status, data);
            }

            return data;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(error.message || '网络错误', 0, null);
        }
    }

    /**
     * GET 请求
     */
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                // 处理数组参数：每个元素作为独立的参数
                if (Array.isArray(value)) {
                    value.forEach(item => {
                        if (item !== null && item !== undefined && item !== '') {
                            searchParams.append(key, item);
                        }
                    });
                } else {
                    searchParams.append(key, value);
                }
            }
        });
        const query = searchParams.toString();
        const url = query ? `${endpoint}?${query}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST 请求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: data,
        });
    }

    /**
     * PUT 请求
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data,
        });
    }

    /**
     * DELETE 请求
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * 上传文件
     */
    async upload(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData,
        });
    }
}

/**
 * API 错误类
 */
class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }
}

// 创建 API 客户端实例
const api = new ApiClient(API_BASE_URL);

/**
 * 统计分析 API
 */
const analysisApi = {
    /**
     * 获取统计数据
     */
    getStatistics() {
        return api.get('/analysis/statistics');
    },

    /**
     * RAG 智能查询
     * @param {string} query - 查询文本
     * @param {number} topK - 返回结果数量
     * @param {Object} filters - 过滤条件
     */
    query(query, topK = 5, filters = null) {
        return api.post('/analysis/query', {
            query,
            top_k: topK,
            filters,
        });
    },

    /**
     * RAG 智能查询（带统计分析）
     * @param {string} query - 查询文本
     * @param {number} topK - 返回结果数量
     * @param {Object} filters - 过滤条件
     * @returns {Promise<Object>} 包含分析结论、来源和统计数据的响应
     */
    queryWithAnalytics(query, topK = 10, filters = null) {
        return api.post('/analysis/query-with-analytics', {
            query,
            top_k: topK,
            filters,
        });
    },
};

/**
 * 筛选条件 API
 */
const conditionsApi = {
    /**
     * 获取筛选条件列表
     * @param {Object} params - 查询参数
     */
    getList(params = {}) {
        return api.get('/conditions', params);
    },

    /**
     * 创建筛选条件
     * @param {Object} data - 条件数据
     */
    create(data) {
        return api.post('/conditions', data);
    },

    /**
     * 更新筛选条件
     * @param {string} id - 条件 ID
     * @param {Object} data - 更新数据
     */
    update(id, data) {
        return api.put(`/conditions/${id}`, data);
    },

    /**
     * 删除筛选条件
     * @param {string} id - 条件 ID
     */
    delete(id) {
        return api.delete(`/conditions/${id}`);
    },

    /**
     * 解析自然语言描述
     * @param {string} text - 自然语言描述
     */
    parseNaturalLanguage(text) {
        return api.post('/conditions/parse-natural-language', { text });
    },
};

/**
 * 人才管理 API
 */
const talentsApi = {
    /**
     * 获取人才列表
     * @param {Object} params - 查询参数
     */
    getList(params = {}) {
        return api.get('/talents', params);
    },

    /**
     * 获取人才详情
     * @param {string} id - 人才 ID
     */
    getDetail(id) {
        return api.get(`/talents/${id}`);
    },

    /**
     * 上传简历并筛选
     * @param {File} file - 简历文件
     * @param {string|null} conditionId - 筛选条件 ID
     * @param {Function} onProgress - 进度回调
     */
    async uploadAndScreen(file, conditionId = null, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        const url = conditionId 
            ? `/talents/upload-screen?condition_id=${conditionId}`
            : '/talents/upload-screen';

        return api.upload(url, formData);
    },

    /**
     * 批量上传简历
     * @param {FileList|File[]} files - 简历文件列表
     * @param {Object|string|null} filterConfig - 筛选配置对象或条件 ID
     */
    async batchUpload(files, filterConfig = null) {
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }
        
        const params = new URLSearchParams();
        if (filterConfig) {
            if (typeof filterConfig === 'string') {
                // 向后兼容：直接是 condition_id
                params.append('condition_id', filterConfig);
            } else {
                // 新格式：完整筛选配置
                params.append('filter_config', JSON.stringify(filterConfig));
            }
        }
        
        const url = params.toString() 
            ? `/talents/batch-upload?${params.toString()}`
            : '/talents/batch-upload';

        return api.upload(url, formData);
    },

    /**
     * 获取任务状态
     * @param {string} taskId - 任务 ID
     */
    getTaskStatus(taskId) {
        return api.get(`/talents/tasks/${taskId}`);
    },

    /**
     * 获取任务列表
     * @param {Object} params - 查询参数
     */
    getTaskList(params = {}) {
        return api.get('/talents/tasks', params);
    },

    /**
     * 取消任务
     * @param {string} taskId - 任务 ID
     */
    cancelTask(taskId) {
        return api.post(`/talents/tasks/${taskId}/cancel`);
    },

    /**
     * 向量化人才
     * @param {string} id - 人才 ID
     */
    vectorize(id) {
        return api.post(`/talents/${id}/vectorize`);
    },

    /**
     * 批量向量化
     * @param {string} screeningStatus - 筛选状态
     * @param {number} limit - 数量限制
     */
    batchVectorize(screeningStatus = 'qualified', limit = 100) {
        return api.post(`/talents/batch-vectorize?screening_status=${screeningStatus}&limit=${limit}`);
    },

    /**
     * 删除人才（逻辑删除）
     * @param {string} id - 人才 ID
     */
    delete(id) {
        return api.delete(`/talents/${id}`);
    },

    /**
     * 恢复已删除的人才
     * @param {string} id - 人才 ID
     */
    restore(id) {
        return api.post(`/talents/${id}/restore`);
    },

    /**
     * 更新人才信息
     * @param {string} id - 人才 ID
     * @param {Object} data - 更新数据
     */
    update(id, data) {
        return api.put(`/talents/${id}`, data);
    },

    /**
     * 批量删除人才
     * @param {string[]} ids - 人才 ID 列表
     */
    batchDelete(ids) {
        return api.post('/talents/batch-delete', { ids });
    },

    /**
     * 批量更新筛选状态
     * @param {string[]} ids - 人才 ID 列表
     * @param {string} screeningStatus - 筛选状态
     */
    batchUpdateStatus(ids, screeningStatus) {
        return api.post('/talents/batch-update-status', { ids, screening_status: screeningStatus });
    },
};

/**
 * 健康检查 API
 */
const healthApi = {
    /**
     * 检查系统健康状态
     */
    check() {
        return fetch('http://localhost:8000/health').then(res => res.json());
    },
};

/**
 * 认证 API
 */
const authApi = {
    /**
     * 用户登录
     * @param {string} username - 用户名
     * @param {string} password - 密码
     */
    async login(username, password) {
        const response = await api.post('/auth/login', { username, password });
        if (response.success && response.data) {
            setStoredToken(response.data.access_token);
            setStoredUser(response.data.user);
            window.dispatchEvent(new CustomEvent('auth:login', { detail: response.data.user }));
        }
        return response;
    },

    /**
     * 用户登出
     */
    async logout() {
        try {
            await api.post('/auth/logout');
        } catch (e) {
            // 忽略登出错误
        }
        clearAuth();
        window.dispatchEvent(new CustomEvent('auth:logout'));
    },

    /**
     * 获取当前用户信息
     */
    async getMe() {
        const response = await api.get('/auth/me');
        if (response.success && response.data) {
            setStoredUser(response.data);
        }
        return response;
    },

    /**
     * 修改密码
     * @param {string} oldPassword - 旧密码
     * @param {string} newPassword - 新密码
     */
    changePassword(oldPassword, newPassword) {
        return api.put('/auth/password', {
            old_password: oldPassword,
            new_password: newPassword,
        });
    },

    /**
     * 检查是否已登录
     */
    isLoggedIn() {
        return !!getStoredToken();
    },

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        return getStoredUser();
    },
};

/**
 * 用户管理 API（管理员）
 */
const usersApi = {
    /**
     * 创建用户
     * @param {Object} data - 用户数据
     */
    create(data) {
        return api.post('/users', data);
    },

    /**
     * 获取用户列表
     * @param {Object} params - 查询参数
     */
    getList(params = {}) {
        return api.get('/users', params);
    },

    /**
     * 更新用户
     * @param {string} id - 用户 ID
     * @param {Object} data - 更新数据
     */
    update(id, data) {
        return api.put(`/users/${id}`, data);
    },

    /**
     * 禁用用户
     * @param {string} id - 用户 ID
     */
    delete(id) {
        return api.delete(`/users/${id}`);
    },

    /**
     * 永久删除用户
     * @param {string} id - 用户 ID
     */
    permanentDelete(id) {
        return api.delete(`/users/${id}/permanent`);
    },

    /**
     * 重置用户密码
     * @param {string} id - 用户 ID
     * @param {string} newPassword - 新密码
     */
    resetPassword(id, newPassword) {
        return api.post(`/users/${id}/reset-password`, { new_password: newPassword });
    },
};

// 导出 API 模块
window.api = api;
window.ApiError = ApiError;
window.analysisApi = analysisApi;
window.conditionsApi = conditionsApi;
window.talentsApi = talentsApi;
window.healthApi = healthApi;
window.authApi = authApi;
window.usersApi = usersApi;
window.getStoredToken = getStoredToken;
window.getStoredUser = getStoredUser;
window.setStoredToken = setStoredToken;
window.setStoredUser = setStoredUser;
window.clearAuth = clearAuth;
