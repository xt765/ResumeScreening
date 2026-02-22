/**
 * API 封装模块
 * 提供与后端 FastAPI 的通信接口
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

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
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

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
                throw new ApiError(data.message || '请求失败', response.status, data);
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
     * @param {string|null} conditionId - 筛选条件 ID
     */
    async batchUpload(files, conditionId = null) {
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }
        
        const url = conditionId 
            ? `/talents/batch-upload?condition_id=${conditionId}`
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

// 导出 API 模块
window.api = api;
window.ApiError = ApiError;
window.analysisApi = analysisApi;
window.conditionsApi = conditionsApi;
window.talentsApi = talentsApi;
window.healthApi = healthApi;
