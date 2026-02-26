/**
 * 数据分析模块
 * 提供 RAG 智能查询、统计分析、候选人列表展示功能
 * 使用 ECharts 进行数据可视化
 * 支持异步任务处理、进度显示、结果导出
 */

const AnalysisPage = {
    /** 查询结果数据 */
    queryResults: null,
    /** ECharts 实例缓存 */
    charts: {},
    /** 学历配色方案 */
    educationColors: {
        '博士': '#7c3aed',
        '硕士': '#3b82f6',
        '本科': '#10b981',
        '大专': '#f59e0b',
        '高中及以下': '#6b7280',
    },
    /** 相似度配色方案 */
    similarityColors: {
        low: '#ef4444',
        medium: '#f59e0b',
        high: '#10b981',
    },

    /** 任务管理属性 */
    currentTaskId: null,
    TASK_ID_KEY: 'analysis_task_id',
    ws: null,
    pollingInterval: null,
    usePolling: false,
    wsRetryCount: 0,
    WS_MAX_RETRY: 3,
    POLLING_INTERVAL: 2000,

    /**
     * 保存任务ID到 localStorage
     * @param {string} taskId - 任务ID
     */
    saveTaskId(taskId) {
        if (taskId) {
            localStorage.setItem(this.TASK_ID_KEY, taskId);
        }
    },

    /**
     * 清除任务ID
     */
    clearTaskId() {
        localStorage.removeItem(this.TASK_ID_KEY);
    },

    /**
     * 获取保存的任务ID
     * @returns {string|null} 任务ID
     */
    getSavedTaskId() {
        return localStorage.getItem(this.TASK_ID_KEY);
    },

    /**
     * 渲染页面
     * @returns {string} 页面HTML
     */
    render() {
        return this.renderContent();
    },

    /**
     * 渲染页面内容
     * @returns {string} HTML字符串
     */
    renderContent() {
        return `
            <div class="analysis-page">
                <!-- RAG 智能查询区域 -->
                <div class="query-section card">
                    <div class="card-body">
                        <div class="query-form">
                            <div class="form-group query-input-group">
                                <label class="form-label">智能查询</label>
                                <textarea 
                                    class="form-control query-textarea" 
                                    id="queryInput" 
                                    rows="3" 
                                    placeholder="输入查询条件，如：有3年以上Python开发经验、硕士学历的候选人"></textarea>
                            </div>
                            <div class="query-actions">
                                <div class="form-group">
                                    <label class="form-label">返回数量</label>
                                    <select class="form-control" id="topKSelect">
                                        <option value="5">5 条</option>
                                        <option value="10" selected>10 条</option>
                                        <option value="15">15 条</option>
                                        <option value="20">20 条</option>
                                        <option value="50">50 条</option>
                                    </select>
                                </div>
                                <button class="btn btn-primary query-btn" id="queryBtn">
                                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="11" cy="11" r="8"/>
                                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                                    </svg>
                                    开始分析
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 进度区域 -->
                <div class="progress-section card" id="progressSection" style="display: none;">
                    <div class="card-header">
                        <h3 class="card-title">
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
                                <path d="M12 6v6l4 2"/>
                            </svg>
                            分析进度
                        </h3>
                        <button class="btn btn-ghost btn-sm" id="cancelAnalysisBtn">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="15" y1="9" x2="9" y2="15"/>
                                <line x1="9" y1="9" x2="15" y2="15"/>
                            </svg>
                            取消任务
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="progress-info">
                            <div class="progress-bar-container">
                                <div class="progress-bar" id="analysisProgressBar" style="width: 0%"></div>
                            </div>
                            <div class="progress-text">
                                <span id="analysisProgressText">0%</span>
                                <span id="analysisProgressMessage">准备中...</span>
                            </div>
                        </div>
                        <div class="progress-hint">
                            <small class="text-muted">
                                任务正在后台处理，您可以切换到其他页面，稍后回来查看结果
                            </small>
                        </div>
                    </div>
                </div>

                <!-- 分析结果区域（查询后显示） -->
                <div class="results-section" id="resultsSection" style="display: none;">
                    <!-- 分析结论卡片 -->
                    <div class="card conclusion-card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
                                    <path d="M12 6v6l4 2"/>
                                </svg>
                                智能分析结论
                            </h3>
                            <div class="card-actions">
                                <button class="btn btn-outline btn-sm" id="exportResultBtn">
                                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                        <polyline points="7 10 12 15 17 10"/>
                                        <line x1="12" y1="15" x2="12" y2="3"/>
                                    </svg>
                                    导出报告
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="conclusion-content" id="conclusionContent"></div>
                        </div>
                    </div>

                    <!-- 查询结果统计仪表板 -->
                    <div class="analytics-dashboard">
                        <!-- 核心指标卡片 -->
                        <div class="metrics-row">
                            <div class="metric-card" style="grid-column: span 2;">
                                <div class="metric-icon primary">
                                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                                        <circle cx="9" cy="7" r="4"/>
                                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                    </svg>
                                </div>
                                <div class="metric-info">
                                    <div class="metric-value" id="totalCount">0</div>
                                    <div class="metric-label">匹配人数</div>
                                </div>
                            </div>
                        </div>

                        <!-- 图表区域 -->
                        <div class="charts-row">
                            <div class="card chart-card">
                                <div class="card-header">
                                    <h4 class="card-title">学历分布</h4>
                                </div>
                                <div class="card-body">
                                    <div id="educationChart" class="chart-container"></div>
                                </div>
                            </div>
                            <div class="card chart-card">
                                <div class="card-header">
                                    <h4 class="card-title">经验分布</h4>
                                </div>
                                <div class="card-body">
                                    <div id="experienceChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>

                        <div class="charts-row">
                            <div class="card chart-card">
                                <div class="card-header">
                                    <h4 class="card-title">热门技能 Top10</h4>
                                </div>
                                <div class="card-body">
                                    <div id="skillsChart" class="chart-container"></div>
                                </div>
                            </div>
                            <div class="card chart-card">
                                <div class="card-header">
                                    <h4 class="card-title">热门学校 Top5</h4>
                                </div>
                                <div class="card-body">
                                    <div id="schoolsChart" class="chart-container"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 候选人列表 -->
                    <div class="card candidates-card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                                    <circle cx="9" cy="7" r="4"/>
                                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                </svg>
                                候选人列表
                            </h3>
                        </div>
                        <div class="card-body">
                            <div class="candidates-list" id="candidatesList"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 初始化事件监听
     */
    initEvents() {
        const queryBtn = document.getElementById('queryBtn');
        if (queryBtn) {
            queryBtn.addEventListener('click', () => this.executeQuery());
        }

        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    this.executeQuery();
                }
            });
        }

        const cancelAnalysisBtn = document.getElementById('cancelAnalysisBtn');
        if (cancelAnalysisBtn) {
            cancelAnalysisBtn.addEventListener('click', () => this.cancelTask());
        }

        const exportResultBtn = document.getElementById('exportResultBtn');
        if (exportResultBtn) {
            exportResultBtn.addEventListener('click', () => this.exportResult());
        }

        this.initWebSocket();
        this.restoreTaskProgress();
    },

    /**
     * 执行查询（异步任务模式）
     */
    async executeQuery() {
        const queryInput = document.getElementById('queryInput');
        const topKSelect = document.getElementById('topKSelect');

        if (!queryInput) return;

        const query = queryInput.value.trim();
        if (!query) {
            UI.toast('请输入查询条件', 'warning');
            return;
        }

        const topK = parseInt(topKSelect?.value || '10');

        try {
            const response = await analysisApi.createQueryTask(query, topK);

            if (response.success) {
                this.currentTaskId = response.data.task_id;
                this.saveTaskId(this.currentTaskId);

                this.showProgressUI(response.data);

                this.subscribeToTask(this.currentTaskId);

                UI.toast('分析任务已创建，正在后台处理...', 'info');
            }
        } catch (error) {
            console.error('创建任务失败:', error);
            UI.toast(error.message || '创建任务失败', 'error');
        }
    },

    /**
     * 显示进度界面
     * @param {Object} taskData - 任务数据
     */
    showProgressUI(taskData) {
        const resultsSection = document.getElementById('resultsSection');
        const progressSection = document.getElementById('progressSection');

        if (resultsSection) resultsSection.style.display = 'none';
        if (progressSection) {
            progressSection.style.display = 'block';
            this.updateProgressUI(taskData);
        }
    },

    /**
     * 隐藏进度界面
     */
    hideProgressUI() {
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    },

    /**
     * 更新进度UI
     * @param {Object} taskData - 任务数据
     */
    updateProgressUI(taskData) {
        const progressBar = document.getElementById('analysisProgressBar');
        const progressText = document.getElementById('analysisProgressText');
        const progressMessage = document.getElementById('analysisProgressMessage');

        const progress = taskData.progress || {};
        const percentage = progress.percentage || 0;

        if (progressBar) progressBar.style.width = `${percentage}%`;
        if (progressText) progressText.textContent = `${Math.round(percentage)}%`;
        if (progressMessage) progressMessage.textContent = progress.message || '处理中...';

        if (taskData.status === 'completed') {
            this.clearTaskId();
            this.stopPolling();
            this.hideProgressUI();
            this.queryResults = taskData.result;
            this.showResults();
            UI.toast('分析完成', 'success');
        }

        if (taskData.status === 'failed') {
            this.clearTaskId();
            this.stopPolling();
            this.hideProgressUI();
            UI.toast(taskData.error || '分析失败', 'error');
        }

        if (taskData.status === 'cancelled') {
            this.clearTaskId();
            this.stopPolling();
            this.hideProgressUI();
            UI.toast('任务已取消', 'info');
        }
    },

    /**
     * 初始化 WebSocket 连接
     */
    initWebSocket() {
        const wsUrl = 'ws://localhost:8000/ws/tasks';

        if (this.usePolling) {
            console.log('使用轮询模式（WebSocket降级）');
            return;
        }

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('AnalysisPage WebSocket 连接已建立');
                this.wsRetryCount = 0;

                if (this.currentTaskId) {
                    this.subscribeToTask(this.currentTaskId);
                }
            };

            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };

            this.ws.onclose = () => {
                console.log('AnalysisPage WebSocket 连接已关闭');
                this.wsRetryCount++;

                if (this.wsRetryCount >= this.WS_MAX_RETRY) {
                    console.log('WebSocket 重试次数超限，切换到轮询模式');
                    this.usePolling = true;
                } else if (this.currentTaskId) {
                    setTimeout(() => this.initWebSocket(), 3000);
                }
            };

            this.ws.onerror = (error) => {
                console.error('AnalysisPage WebSocket 错误:', error);
            };
        } catch (error) {
            console.error('WebSocket 初始化失败:', error);
            this.usePolling = true;
        }
    },

    /**
     * 处理 WebSocket 消息
     * @param {Object} message - 消息对象
     */
    handleWebSocketMessage(message) {
        if (message.type === 'task_update' && message.task_id === this.currentTaskId) {
            this.updateProgressUI(message.data);
        }
    },

    /**
     * 订阅任务进度
     * @param {string} taskId - 任务ID
     */
    subscribeToTask(taskId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'subscribe',
                task_id: taskId
            }));
        } else {
            this.startPolling();
        }
    },

    /**
     * 开始轮询
     */
    startPolling() {
        if (this.pollingInterval) {
            return;
        }

        console.log('启动轮询模式');
        this.pollingInterval = setInterval(async () => {
            if (!this.currentTaskId) {
                return;
            }

            try {
                const response = await analysisApi.getTaskStatus(this.currentTaskId);
                if (response.success && response.data) {
                    this.updateProgressUI(response.data);
                }
            } catch (error) {
                console.error('轮询任务状态失败:', error);
            }
        }, this.POLLING_INTERVAL);
    },

    /**
     * 停止轮询
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('轮询已停止');
        }
    },

    /**
     * 恢复任务进度显示
     */
    async restoreTaskProgress() {
        const savedTaskId = this.getSavedTaskId();
        if (!savedTaskId) {
            return;
        }

        try {
            const response = await analysisApi.getTaskStatus(savedTaskId);
            if (response.success && response.data) {
                const taskData = response.data;

                if (['pending', 'running'].includes(taskData.status)) {
                    this.currentTaskId = savedTaskId;
                    this.showProgressUI(taskData);
                    this.subscribeToTask(savedTaskId);
                } else if (taskData.status === 'completed') {
                    this.clearTaskId();
                    this.queryResults = taskData.result;
                    this.showResults();
                } else {
                    this.clearTaskId();
                }
            }
        } catch (error) {
            console.error('恢复任务进度失败:', error);
            this.clearTaskId();
        }
    },

    /**
     * 取消任务
     */
    async cancelTask() {
        if (!this.currentTaskId) return;

        try {
            const response = await talentsApi.cancelTask(this.currentTaskId);
            if (response.success) {
                this.clearTaskId();
                this.stopPolling();
                this.hideProgressUI();
                UI.toast('任务已取消', 'info');
            }
        } catch (error) {
            console.error('取消任务失败:', error);
            UI.toast(error.message || '取消任务失败', 'error');
        }
    },

    /**
     * 导出结果
     */
    exportResult() {
        if (!this.currentTaskId && !this.queryResults?.query_id) {
            UI.toast('没有可导出的结果', 'warning');
            return;
        }

        const taskId = this.currentTaskId || this.queryResults.query_id;
        const token = getStoredToken();
        const url = `${API_BASE_URL}/analysis/tasks/${taskId}/export?token=${token}`;
        window.open(url, '_blank');
    },

    /**
     * 显示查询结果
     */
    showResults() {
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection || !this.queryResults) return;

        resultsSection.style.display = 'block';

        const data = this.queryResults;

        this.renderConclusion(data.answer);
        this.renderAnalytics(data.analytics);
        this.renderCandidates(data.sources);

        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    /**
     * 渲染分析结论（支持 Markdown）
     * @param {string} answer - LLM生成的分析结论
     */
    renderConclusion(answer) {
        const container = document.getElementById('conclusionContent');
        if (!container) return;

        if (!answer) {
            container.innerHTML = '<div class="text-muted">暂无分析结论</div>';
            return;
        }

        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
            });
            let html = marked.parse(answer);
            html = html.replace(/<strong>([^\s【】*]+)[：:]\s*(\d+分[^<]*)<\/strong>/g, 
                '<strong><span class="candidate-name-highlight" onclick="AnalysisPage.scrollToCandidateByName(\'$1\')">$1</span>：$2</strong>');
            container.innerHTML = html;
        } else {
            let formatted = answer
                .replace(/###\s*(.+)/g, '<h5 class="conclusion-section">$1</h5>')
                .replace(/##\s*(.+)/g, '<h4 class="conclusion-heading">$1</h4>')
                .replace(/#\s*(.+)/g, '<h3 class="conclusion-title">$1</h3>')
                .replace(/\*\*([^\s【】*]+)[：:]\s*(\d+分[^\*]*)\*\*/g, 
                    '<strong><span class="candidate-name-highlight" onclick="AnalysisPage.scrollToCandidateByName(\'$1\')">$1</span>：$2</strong>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
                .replace(/^- (.+)$/gm, '<li>$1</li>')
                .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
                .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
            container.innerHTML = `<p>${formatted}</p>`;
        }
    },

    /**
     * 滚动到指定候选人卡片并高亮
     * @param {number} index - 候选人索引（从1开始）
     */
    scrollToCandidate(index) {
        const candidateCards = document.querySelectorAll('.candidate-card');
        const targetCard = candidateCards[index - 1];
        
        if (targetCard) {
            candidateCards.forEach(card => card.classList.remove('highlight'));
            
            targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            targetCard.classList.add('highlight');
            
            setTimeout(() => {
                targetCard.classList.remove('highlight');
            }, 3000);
        }
    },

    /**
     * 根据姓名滚动到候选人卡片并高亮
     * @param {string} name - 候选人姓名
     */
    scrollToCandidateByName(name) {
        if (!name) return;
        
        const candidateCards = document.querySelectorAll('.candidate-card');
        
        for (const card of candidateCards) {
            const nameElement = card.querySelector('.candidate-name');
            if (nameElement && nameElement.textContent.includes(name)) {
                candidateCards.forEach(c => c.classList.remove('highlight'));
                
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                card.classList.add('highlight');
                
                setTimeout(() => {
                    card.classList.remove('highlight');
                }, 3000);
                
                break;
            }
        }
    },

    /**
     * 渲染统计数据
     * @param {Object} analytics - 统计数据
     */
    renderAnalytics(analytics) {
        if (!analytics) return;

        const totalCount = document.getElementById('totalCount');

        if (totalCount) {
            totalCount.textContent = analytics.total_count || 0;
        }

        setTimeout(() => {
            this.renderEducationChart(analytics.by_education);
            this.renderExperienceChart(analytics.by_work_years_range);
            this.renderSkillsChart(analytics.top_skills);
            this.renderSchoolsChart(analytics.top_schools);
        }, 100);
    },

    /**
     * 渲染学历分布图表
     * @param {Object} data - 学历分布数据
     */
    renderEducationChart(data) {
        const container = document.getElementById('educationChart');
        if (!container || typeof echarts === 'undefined') return;

        if (this.charts.education) {
            this.charts.education.dispose();
        }

        const chart = echarts.init(container);
        this.charts.education = chart;

        if (!data || Object.keys(data).length === 0) {
            chart.setOption({
                title: {
                    text: '暂无数据',
                    left: 'center',
                    top: 'center',
                    textStyle: { color: '#9ca3af', fontSize: 14 }
                }
            });
            return;
        }

        const order = ['博士', '硕士', '本科', '大专', '高中及以下'];
        const sortedData = order
            .filter(key => data[key])
            .map(key => ({
                name: key,
                value: data[key],
                itemStyle: { color: this.educationColors[key] || '#6b7280' }
            }));

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            grid: {
                left: '3%',
                right: '8%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: '#e5e7eb', type: 'dashed' } }
            },
            yAxis: {
                type: 'category',
                data: sortedData.map(d => d.name),
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: '#374151' }
            },
            series: [{
                type: 'bar',
                data: sortedData,
                barWidth: '60%',
                label: {
                    show: true,
                    position: 'right',
                    color: '#374151',
                    fontWeight: 500
                },
                itemStyle: {
                    borderRadius: [0, 4, 4, 0]
                }
            }]
        };

        chart.setOption(option);
        window.addEventListener('resize', () => chart.resize());
    },

    /**
     * 渲染经验分布图表
     * @param {Object} data - 经验分布数据
     */
    renderExperienceChart(data) {
        const container = document.getElementById('experienceChart');
        if (!container || typeof echarts === 'undefined') return;

        if (this.charts.experience) {
            this.charts.experience.dispose();
        }

        const chart = echarts.init(container);
        this.charts.experience = chart;

        if (!data || Object.keys(data).length === 0) {
            chart.setOption({
                title: {
                    text: '暂无数据',
                    left: 'center',
                    top: 'center',
                    textStyle: { color: '#9ca3af', fontSize: 14 }
                }
            });
            return;
        }

        const order = ['0-3年', '3-5年', '5-10年', '10年以上'];
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

        const sortedData = order
            .filter(key => data[key])
            .map((key, index) => ({
                name: key,
                value: data[key],
                itemStyle: { color: colors[index] || '#6b7280' }
            }));

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            grid: {
                left: '3%',
                right: '8%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: '#e5e7eb', type: 'dashed' } }
            },
            yAxis: {
                type: 'category',
                data: sortedData.map(d => d.name),
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: '#374151' }
            },
            series: [{
                type: 'bar',
                data: sortedData,
                barWidth: '60%',
                label: {
                    show: true,
                    position: 'right',
                    color: '#374151',
                    fontWeight: 500
                },
                itemStyle: {
                    borderRadius: [0, 4, 4, 0]
                }
            }]
        };

        chart.setOption(option);
        window.addEventListener('resize', () => chart.resize());
    },

    /**
     * 渲染热门技能图表
     * @param {Array} data - 技能数据
     */
    renderSkillsChart(data) {
        const container = document.getElementById('skillsChart');
        if (!container || typeof echarts === 'undefined') return;

        if (this.charts.skills) {
            this.charts.skills.dispose();
        }

        const chart = echarts.init(container);
        this.charts.skills = chart;

        if (!data || data.length === 0) {
            chart.setOption({
                title: {
                    text: '暂无数据',
                    left: 'center',
                    top: 'center',
                    textStyle: { color: '#9ca3af', fontSize: 14 }
                }
            });
            return;
        }

        const topSkills = data.slice(0, 10).reverse();

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            grid: {
                left: '3%',
                right: '8%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: '#e5e7eb', type: 'dashed' } }
            },
            yAxis: {
                type: 'category',
                data: topSkills.map(d => d.name),
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: '#374151' }
            },
            series: [{
                type: 'bar',
                data: topSkills.map(d => d.count),
                barWidth: '60%',
                label: {
                    show: true,
                    position: 'right',
                    color: '#374151',
                    fontWeight: 500
                },
                itemStyle: {
                    color: '#3b82f6',
                    borderRadius: [0, 4, 4, 0]
                }
            }]
        };

        chart.setOption(option);
        window.addEventListener('resize', () => chart.resize());
    },

    /**
     * 渲染热门学校图表
     * @param {Array} data - 学校数据
     */
    renderSchoolsChart(data) {
        const container = document.getElementById('schoolsChart');
        if (!container || typeof echarts === 'undefined') return;

        if (this.charts.schools) {
            this.charts.schools.dispose();
        }

        const chart = echarts.init(container);
        this.charts.schools = chart;

        if (!data || data.length === 0) {
            chart.setOption({
                title: {
                    text: '暂无数据',
                    left: 'center',
                    top: 'center',
                    textStyle: { color: '#9ca3af', fontSize: 14 }
                }
            });
            return;
        }

        const topSchools = data.slice(0, 5).reverse();

        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            grid: {
                left: '3%',
                right: '8%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: '#e5e7eb', type: 'dashed' } }
            },
            yAxis: {
                type: 'category',
                data: topSchools.map(d => d.name),
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: {
                    color: '#374151',
                    width: 100,
                    overflow: 'truncate',
                    ellipsis: '...'
                }
            },
            series: [{
                type: 'bar',
                data: topSchools.map(d => d.count),
                barWidth: '60%',
                label: {
                    show: true,
                    position: 'right',
                    color: '#374151',
                    fontWeight: 500
                },
                itemStyle: {
                    color: '#10b981',
                    borderRadius: [0, 4, 4, 0]
                }
            }]
        };

        chart.setOption(option);
        window.addEventListener('resize', () => chart.resize());
    },

    /**
     * 渲染候选人列表
     * @param {Array} sources - 候选人数据
     */
    renderCandidates(sources) {
        const container = document.getElementById('candidatesList');
        if (!container) return;

        if (!sources || sources.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无匹配的候选人</div>';
            return;
        }

        const answer = this.queryResults?.answer || '';
        const scores = this.parseAllRecommendationScores(answer);
        
        const sortedSources = [...sources].sort((a, b) => {
            const nameA = a.metadata?.name || '';
            const nameB = b.metadata?.name || '';
            const scoreA = scores[nameA] || 0;
            const scoreB = scores[nameB] || 0;
            
            if (scoreA !== scoreB) {
                return scoreB - scoreA;
            }
            
            if (a.similarity_score !== undefined && b.similarity_score !== undefined) {
                return b.similarity_score - a.similarity_score;
            }
            
            return 0;
        });

        container.innerHTML = sortedSources.map((source, index) => {
            const metadata = source.metadata || {};
            const candidateIndex = index + 1;
            const name = metadata.name || '';
            
            let recommendationScore = scores[name] || null;
            
            if (recommendationScore === null && source.similarity_score !== undefined) {
                recommendationScore = Math.round(source.similarity_score * 100);
            }
            
            let scoreHtml = '';
            if (recommendationScore !== null) {
                const scoreClass = this.getScoreClass(recommendationScore);
                scoreHtml = this.renderScoreCircle(recommendationScore, scoreClass);
            }

            return `
                <div class="candidate-card" data-id="${source.id}">
                    <div class="candidate-rank">${candidateIndex}</div>
                    <div class="candidate-info">
                        <div class="candidate-header">
                            <span class="candidate-name">${this.escapeHtml(name || '未知')}</span>
                            <span class="candidate-education" style="color: ${this.educationColors[this.getEducationLabel(metadata.education_level)] || '#374151'}">
                                ${this.getEducationLabel(metadata.education_level) || '-'}
                            </span>
                        </div>
                        <div class="candidate-details">
                            ${metadata.school ? `<span class="detail-item"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>${this.escapeHtml(metadata.school)}</span>` : ''}
                            ${metadata.work_years !== undefined ? `<span class="detail-item"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>${metadata.work_years}年经验</span>` : ''}
                            ${metadata.position ? `<span class="detail-item"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>${this.escapeHtml(metadata.position)}</span>` : ''}
                        </div>
                        ${(() => {
                            let skills = metadata.skills;
                            if (typeof skills === 'string' && skills) {
                                skills = skills.split(',').map(s => s.trim()).filter(s => s);
                            } else if (!Array.isArray(skills)) {
                                skills = [];
                            }
                            if (skills.length > 0) {
                                return `
                                    <div class="candidate-skills">
                                        ${skills.slice(0, 5).map(skill => `<span class="skill-tag">${this.escapeHtml(skill)}</span>`).join('')}
                                        ${skills.length > 5 ? `<span class="skill-more">+${skills.length - 5}</span>` : ''}
                                    </div>
                                `;
                            }
                            return '';
                        })()}
                    </div>
                    ${scoreHtml}
                    <div class="candidate-actions">
                        <button class="btn btn-sm btn-outline" onclick="AnalysisPage.viewTalentDetail('${source.id}')">
                            查看详情
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * 从 LLM 回答中解析所有候选人的推荐指数
     * @param {string} answer - LLM 回答
     * @returns {Object} 姓名到评分的映射 { name: score }
     */
    parseAllRecommendationScores(answer) {
        if (!answer) return {};
        
        const scores = {};
        const patterns = [
            /\*\*([^\s【】*]+)[：:]\s*(\d+)分/g,
            /([^\s【】*]+)[：:]\s*(\d+)分/g
        ];
        
        for (const pattern of patterns) {
            let match;
            while ((match = pattern.exec(answer)) !== null) {
                const name = match[1].trim();
                const score = parseInt(match[2], 10);
                if (name && score && !scores[name]) {
                    scores[name] = score;
                }
            }
        }
        
        return scores;
    },

    /**
     * 从 LLM 回答中解析候选人的推荐指数（旧方法，保留兼容）
     * @param {string} answer - LLM 回答
     * @param {number} candidateIndex - 候选人索引（从1开始）
     * @returns {number|null} 推荐指数
     * @deprecated 使用 parseAllRecommendationScores 代替
     */
    parseRecommendationScore(answer, candidateIndex) {
        if (!answer) return null;
        
        const altPattern = new RegExp(`候选人${candidateIndex}[^\\d]*(\\d+)\\s*分`, 'i');
        const altMatch = answer.match(altPattern);
        
        if (altMatch) {
            return parseInt(altMatch[1], 10);
        }
        
        return null;
    },

    /**
     * 获取相似度样式类
     * @param {number} similarity - 相似度分数
     * @returns {string} 样式类名
     */
    getSimilarityClass(similarity) {
        if (similarity >= 0.8) return 'high';
        if (similarity >= 0.6) return 'medium';
        return 'low';
    },

    /**
     * 获取推荐指数样式类
     * @param {number} score - 推荐指数
     * @returns {string} 样式类名
     */
    getScoreClass(score) {
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        return 'low';
    },

    /**
     * 渲染推荐指数圆形进度条
     * @param {number} score - 推荐指数
     * @param {string} scoreClass - 样式类名
     * @returns {string} HTML字符串
     */
    renderScoreCircle(score, scoreClass) {
        const circumference = 2 * Math.PI * 24;
        const offset = circumference - (score / 100) * circumference;
        
        return `
            <div class="candidate-score ${scoreClass}">
                <div class="score-circle">
                    <svg class="circular-chart" viewBox="0 0 56 56">
                        <circle class="circle-bg" cx="28" cy="28" r="24"/>
                        <circle class="circle" cx="28" cy="28" r="24"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${offset}"/>
                    </svg>
                    <span class="score-text">${score}</span>
                </div>
                <span class="score-label">推荐指数</span>
            </div>
        `;
    },

    /**
     * 获取学历标签
     * @param {string} level - 学历代码
     * @returns {string} 学历标签
     */
    getEducationLabel(level) {
        const labels = {
            'doctor': '博士',
            'master': '硕士',
            'bachelor': '本科',
            'college': '大专',
            'high_school': '高中及以下',
        };
        return labels[level] || level;
    },

    getScreeningStatusLabel(status) {
        const labels = {
            'qualified': '通过',
            'disqualified': '未通过',
            'passed': '通过',
            'failed': '未通过',
            'pending': '待筛选',
        };
        return labels[status] || '待筛选';
    },

    getScreeningStatusClass(status) {
        const classes = {
            'qualified': 'passed',
            'disqualified': 'failed',
            'passed': 'passed',
            'failed': 'failed',
            'pending': 'pending',
        };
        return classes[status] || 'pending';
    },

    async viewTalentDetail(talentId) {
        try {
            // 先显示加载状态的模态框
            const loadingContent = `
                <div style="padding: 40px; text-align: center;">
                    <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite; color: var(--primary-color); margin-bottom: 12px;">
                        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
                    </svg>
                    <div style="color: var(--text-secondary);">正在加载人才详情...</div>
                </div>
            `;
            UI.showModal('人才详情', loadingContent, '', 'lg');

            const response = await talentsApi.getDetail(talentId);
            if (response.success) {
                this.showTalentDetailModal(response.data);
            } else {
                UI.toast('获取人才详情失败', 'error');
                UI.closeModal();
            }
        } catch (error) {
            console.error('获取人才详情失败:', error);
            UI.toast(error.message || '获取人才详情失败', 'error');
            UI.closeModal();
        }
    },

    showTalentDetailModal(talent) {
        const data = talent.metadata || talent;
        let skills = data.skills;
        if (typeof skills === 'string' && skills) {
            skills = skills.split(',').map(s => s.trim()).filter(s => s);
        } else if (!Array.isArray(skills)) {
            skills = [];
        }

        const education = this.getEducationLabel(data.education_level) || data.education_level || '-';
        const statusBadge = data.screening_status === 'qualified' 
            ? '<span class="badge badge-success">通过</span>'
            : (data.screening_status === 'disqualified' 
                ? '<span class="badge badge-danger">未通过</span>' 
                : '<span class="badge badge-warning">待筛选</span>');

        const photoUrl = data.id ? `http://localhost:8000/api/v1/talents/${data.id}/photo` : '';
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
                        <h3 class="detail-name">${this.escapeHtml(data.name || '未知')}</h3>
                        <div class="detail-meta">
                            <span>${education}</span>
                            <span class="separator">|</span>
                            <span>${this.escapeHtml(data.school || '-')}</span>
                            <span class="separator">|</span>
                            <span>${this.escapeHtml(data.major || '-')}</span>
                        </div>
                    </div>
                    <div class="detail-status">${statusBadge}</div>
                </div>

                <div class="detail-section">
                    <h4 class="section-title">基本信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">联系电话</span>
                            <span class="detail-value">${this.escapeHtml(data.phone || '-')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">电子邮箱</span>
                            <span class="detail-value">${this.escapeHtml(data.email || '-')}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">工作年限</span>
                            <span class="detail-value">${data.work_years !== undefined ? data.work_years + ' 年' : '-'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">毕业日期</span>
                            <span class="detail-value">${data.graduation_date || '-'}</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h4 class="section-title">技能标签</h4>
                    <div class="skill-tags">
                        ${skills.length > 0 
                            ? skills.map(skill => `<span class="skill-tag">${this.escapeHtml(skill)}</span>`).join('') 
                            : '<span class="text-muted">暂无技能信息</span>'}
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
                            <span class="detail-value">${UI.formatDateTime(data.screening_date, false)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">创建时间</span>
                            <span class="detail-value">${UI.formatDateTime(data.created_at)}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">更新时间</span>
                            <span class="detail-value">${UI.formatDateTime(data.updated_at)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        UI.showModal('人才详情', content, '', 'lg');
    },

    closeTalentDetailModal() {
        UI.closeModal();
    },

    /**
     * HTML转义
     * @param {string} text - 原始文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * 销毁图表实例
     */
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.dispose();
        });
        this.charts = {};
    },

    /**
     * 页面销毁
     */
    destroy() {
        this.destroyCharts();
        this.stopPolling();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
};

if (!document.getElementById('analysis-styles')) {
    const analysisStyles = document.createElement('style');
    analysisStyles.id = 'analysis-styles';
    analysisStyles.textContent = `
    /* ========================================
       分析页面 - 整体布局
    ======================================== */
    .analysis-page .page-header {
        margin-bottom: 24px;
    }

    .analysis-page .page-title {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }

    .analysis-page .page-desc {
        font-size: 14px;
        color: var(--text-secondary);
    }

    /* ========================================
       查询区域样式
    ======================================== */
    .analysis-page .query-section {
        margin-bottom: 24px;
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid var(--border-color, #e5e7eb);
    }

    .analysis-page .query-form {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .analysis-page .query-input-group {
        flex: 1;
    }

    .analysis-page .query-textarea {
        min-height: 80px;
        resize: vertical;
        font-size: 14px;
        line-height: 1.6;
        border: 2px solid var(--border-color, #e5e7eb);
        transition: all 0.2s ease;
    }

    .analysis-page .query-textarea:focus {
        border-color: var(--primary-color, #3370ff);
        box-shadow: 0 0 0 3px rgba(51, 112, 255, 0.1);
    }

    .analysis-page .query-actions {
        display: flex;
        align-items: flex-end;
        gap: 16px;
    }

    .analysis-page .query-actions .form-group {
        margin-bottom: 0;
        min-width: 120px;
    }

    .analysis-page .query-btn {
        flex-shrink: 0;
        min-width: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: linear-gradient(135deg, var(--primary-color, #3370ff) 0%, #5b8def 100%);
        border: none;
        box-shadow: 0 4px 12px rgba(51, 112, 255, 0.25);
        transition: all 0.3s ease;
    }

    .analysis-page .query-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(51, 112, 255, 0.35);
    }

    .analysis-page .query-btn:active {
        transform: translateY(0);
    }

    /* ========================================
       进度区域样式
    ======================================== */
    .analysis-page .progress-section {
        margin-bottom: 24px;
        border-left: 4px solid var(--primary-color, #3370ff);
        background: linear-gradient(90deg, rgba(51, 112, 255, 0.03) 0%, transparent 100%);
    }

    .analysis-page .progress-info {
        margin-bottom: 12px;
    }

    .analysis-page .progress-bar-container {
        height: 10px;
        background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 100%);
        border-radius: 5px;
        overflow: hidden;
        margin-bottom: 8px;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .analysis-page .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #3370ff, #10b981);
        border-radius: 5px;
        transition: width 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .analysis-page .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: shimmer 2s infinite;
    }

    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .analysis-page .progress-text {
        display: flex;
        justify-content: space-between;
        font-size: 14px;
        color: var(--text-secondary);
    }

    .analysis-page .progress-hint {
        padding-top: 8px;
        border-top: 1px solid var(--border-color, #e5e7eb);
    }

    /* ========================================
       分析结论卡片 - 核心优化区域
    ======================================== */
    .analysis-page .conclusion-card {
        margin-bottom: 24px;
        border-left: 4px solid var(--primary-color, #3370ff);
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }

    .analysis-page .conclusion-card .card-header {
        background: linear-gradient(135deg, rgba(51, 112, 255, 0.05) 0%, rgba(51, 112, 255, 0.02) 100%);
        border-bottom: 1px solid rgba(51, 112, 255, 0.1);
    }

    .analysis-page .conclusion-card .card-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 17px;
        font-weight: 600;
        color: var(--text-primary);
    }

    .analysis-page .conclusion-card .card-title svg {
        color: var(--primary-color, #3370ff);
    }

    .analysis-page .card-actions {
        display: flex;
        gap: 8px;
    }

    /* 报告内容区域 */
    .analysis-page .conclusion-content {
        font-size: 14px;
        line-height: 2;
        color: var(--text-primary);
        padding: 8px 0;
    }

    /* 标题样式 - 增强视觉层次 */
    .analysis-page .conclusion-content h1 {
        font-size: 24px;
        font-weight: 700;
        margin: 28px 0 16px;
        color: var(--text-primary);
        background: linear-gradient(135deg, var(--primary-color, #3370ff) 0%, #5b8def 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        position: relative;
        padding-bottom: 12px;
    }

    .analysis-page .conclusion-content h1::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color, #3370ff), transparent);
        border-radius: 2px;
    }

    .analysis-page .conclusion-content h2 {
        font-size: 20px;
        font-weight: 600;
        margin: 24px 0 14px;
        color: var(--text-primary);
        border-left: 4px solid var(--primary-color, #3370ff);
        padding-left: 16px;
        background: linear-gradient(90deg, rgba(51, 112, 255, 0.05) 0%, transparent 100%);
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }

    .analysis-page .conclusion-content h3 {
        font-size: 18px;
        font-weight: 600;
        margin: 20px 0 12px;
        color: var(--text-primary);
        position: relative;
        padding-left: 20px;
    }

    .analysis-page .conclusion-content h3::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 8px;
        height: 8px;
        background: var(--primary-color, #3370ff);
        border-radius: 50%;
    }

    .analysis-page .conclusion-content h4 {
        font-size: 16px;
        font-weight: 600;
        margin: 18px 0 10px;
        color: #4b5563;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .analysis-page .conclusion-content h4::before {
        content: '▸';
        color: var(--primary-color, #3370ff);
        font-size: 14px;
    }

    .analysis-page .conclusion-content h5 {
        font-size: 15px;
        font-weight: 600;
        margin: 16px 0 8px;
        color: #6b7280;
    }

    .analysis-page .conclusion-content h6 {
        font-size: 14px;
        font-weight: 600;
        margin: 14px 0 6px;
        color: var(--text-muted, #9ca3af);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* 段落样式 */
    .analysis-page .conclusion-content p {
        margin: 0 0 16px;
        line-height: 2;
        text-align: justify;
    }

    /* 列表样式 - 添加自定义图标 */
    .analysis-page .conclusion-content ul,
    .analysis-page .conclusion-content ol {
        margin: 16px 0;
        padding-left: 0;
        list-style: none;
    }

    .analysis-page .conclusion-content ul {
        counter-reset: ul-item;
    }

    .analysis-page .conclusion-content ul > li {
        position: relative;
        padding-left: 28px;
        margin-bottom: 12px;
        line-height: 1.8;
    }

    .analysis-page .conclusion-content ul > li::before {
        content: '';
        position: absolute;
        left: 8px;
        top: 10px;
        width: 6px;
        height: 6px;
        background: var(--primary-color, #3370ff);
        border-radius: 50%;
        box-shadow: 0 0 0 3px rgba(51, 112, 255, 0.2);
    }

    .analysis-page .conclusion-content ol {
        counter-reset: ol-item;
    }

    .analysis-page .conclusion-content ol > li {
        position: relative;
        padding-left: 36px;
        margin-bottom: 12px;
        line-height: 1.8;
        counter-increment: ol-item;
    }

    .analysis-page .conclusion-content ol > li::before {
        content: counter(ol-item);
        position: absolute;
        left: 0;
        top: 2px;
        width: 24px;
        height: 24px;
        background: linear-gradient(135deg, var(--primary-color, #3370ff), #5b8def);
        color: #fff;
        border-radius: 50%;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 6px rgba(51, 112, 255, 0.3);
    }

    .analysis-page .conclusion-content ul ul,
    .analysis-page .conclusion-content ol ol,
    .analysis-page .conclusion-content ul ol,
    .analysis-page .conclusion-content ol ul {
        margin: 8px 0;
        padding-left: 8px;
    }

    .analysis-page .conclusion-content li {
        margin-bottom: 10px;
        line-height: 1.8;
    }

    /* 分隔线 */
    .analysis-page .conclusion-content hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--border-color, #e5e7eb), transparent);
        margin: 28px 0;
    }

    /* 链接样式 */
    .analysis-page .conclusion-content a {
        color: var(--primary-color, #3370ff);
        text-decoration: none;
        border-bottom: 1px dashed var(--primary-color, #3370ff);
        transition: all 0.2s ease;
        padding-bottom: 1px;
    }

    .analysis-page .conclusion-content a:hover {
        color: var(--primary-hover, #2860e1);
        border-bottom-style: solid;
        background: rgba(51, 112, 255, 0.05);
    }

    /* 图片样式 */
    .analysis-page .conclusion-content img {
        max-width: 100%;
        height: auto;
        border-radius: var(--radius-md, 8px);
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* 删除线 */
    .analysis-page .conclusion-content del {
        color: var(--text-muted, #9ca3af);
        text-decoration: line-through;
    }

    /* 行内代码 */
    .analysis-page .conclusion-content code {
        background: linear-gradient(135deg, #fef3f2 0%, #fee2e2 100%);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 13px;
        color: #dc2626;
        font-family: 'Consolas', 'Monaco', monospace;
        border: 1px solid rgba(220, 38, 38, 0.2);
    }

    /* 代码块 */
    .analysis-page .conclusion-content pre {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        color: #e5e7eb;
        padding: 20px;
        border-radius: 12px;
        overflow-x: auto;
        margin: 16px 0;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .analysis-page .conclusion-content pre code {
        background: none;
        color: inherit;
        padding: 0;
        border: none;
        font-size: 13px;
    }

    /* 引用块 - 增强样式 */
    .analysis-page .conclusion-content blockquote {
        border-left: 4px solid var(--primary-color, #3370ff);
        padding: 16px 20px;
        margin: 20px 0;
        color: #4b5563;
        background: linear-gradient(90deg, rgba(51, 112, 255, 0.05) 0%, transparent 100%);
        border-radius: 0 8px 8px 0;
        font-style: italic;
        position: relative;
    }

    .analysis-page .conclusion-content blockquote::before {
        content: '"';
        position: absolute;
        top: 8px;
        left: 12px;
        font-size: 32px;
        color: var(--primary-color, #3370ff);
        opacity: 0.3;
        font-family: Georgia, serif;
    }

    /* 表格样式 - 专业美观 */
    .analysis-page .conclusion-content table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 20px 0;
        font-size: 14px;
        background: #fff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid var(--border-color, #e5e7eb);
    }

    .analysis-page .conclusion-content thead {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }

    .analysis-page .conclusion-content th {
        padding: 14px 18px;
        text-align: left;
        font-weight: 600;
        color: var(--text-primary);
        border-bottom: 2px solid var(--primary-color, #3370ff);
        white-space: nowrap;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .analysis-page .conclusion-content td {
        padding: 14px 18px;
        color: var(--text-primary);
        border-bottom: 1px solid #f3f4f6;
        vertical-align: top;
        transition: background-color 0.2s ease;
    }

    .analysis-page .conclusion-content tbody tr:last-child td {
        border-bottom: none;
    }

    .analysis-page .conclusion-content tbody tr:nth-child(even) {
        background: rgba(248, 250, 252, 0.5);
    }

    .analysis-page .conclusion-content tbody tr:hover {
        background: linear-gradient(90deg, rgba(51, 112, 255, 0.05) 0%, rgba(51, 112, 255, 0.02) 100%);
    }

    .analysis-page .conclusion-content th:first-child,
    .analysis-page .conclusion-content td:first-child {
        padding-left: 24px;
    }

    .analysis-page .conclusion-content th:last-child,
    .analysis-page .conclusion-content td:last-child {
        padding-right: 24px;
    }

    /* 兼容旧样式 */
    .analysis-page .conclusion-heading {
        font-size: 16px;
        font-weight: 600;
        margin: 16px 0 8px;
        color: var(--text-primary);
    }

    .analysis-page .conclusion-section {
        font-size: 14px;
        font-weight: 600;
        margin: 12px 0 6px;
        color: var(--text-secondary);
    }

    /* 候选人姓名高亮 */
    .analysis-page .candidate-name-highlight {
        font-weight: 600;
        color: #1e40af;
        border-bottom: 2px solid #3370ff;
        padding-bottom: 1px;
        cursor: pointer;
        transition: all 0.2s ease;
        background: linear-gradient(to bottom, transparent 60%, rgba(51, 112, 255, 0.15) 60%);
        border-radius: 2px;
    }

    .analysis-page .candidate-name-highlight:hover {
        color: #1d4ed8;
        border-bottom-color: #1d4ed8;
        background: linear-gradient(to bottom, transparent 60%, rgba(51, 112, 255, 0.25) 60%);
        transform: translateY(-1px);
    }

    /* 候选人引用标记 */
    .analysis-page .candidate-ref {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
        height: 20px;
        background: linear-gradient(135deg, var(--primary-color, #3370ff) 0%, #5b8def 100%);
        color: #fff;
        padding: 0 6px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(51, 112, 255, 0.3);
        text-decoration: none;
        vertical-align: middle;
        margin: 0 2px;
        line-height: 1;
    }

    .analysis-page .candidate-ref:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        box-shadow: 0 4px 10px rgba(51, 112, 255, 0.4);
        transform: scale(1.15);
    }

    .analysis-page .candidate-ref:active {
        transform: scale(1);
    }

    /* ========================================
       统计仪表板
    ======================================== */
    .analysis-page .analytics-dashboard {
        margin-bottom: 24px;
    }

    .analysis-page .metrics-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 20px;
    }

    .analysis-page .metric-card {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 24px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: var(--radius-lg, 12px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border: 1px solid var(--border-color, #e5e7eb);
        transition: all 0.3s ease;
    }

    .analysis-page .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }

    .analysis-page .metric-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        border-radius: 14px;
        transition: transform 0.3s ease;
    }

    .analysis-page .metric-card:hover .metric-icon {
        transform: scale(1.1);
    }

    .analysis-page .metric-icon.primary {
        background: linear-gradient(135deg, rgba(51, 112, 255, 0.15) 0%, rgba(51, 112, 255, 0.05) 100%);
        color: var(--primary-color, #3370ff);
    }

    .analysis-page .metric-icon.success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
        color: #10b981;
    }

    .analysis-page .metric-info {
        flex: 1;
    }

    .analysis-page .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
        margin-bottom: 4px;
    }

    .analysis-page .metric-label {
        font-size: 13px;
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* ========================================
       图表卡片
    ======================================== */
    .analysis-page .charts-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 16px;
    }

    .analysis-page .chart-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: var(--radius-lg, 12px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border: 1px solid var(--border-color, #e5e7eb);
        transition: all 0.3s ease;
    }

    .analysis-page .chart-card:hover {
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }

    .analysis-page .chart-card .card-header {
        padding: 18px 22px;
        border-bottom: 1px solid var(--border-color, #e5e7eb);
        background: linear-gradient(90deg, rgba(51, 112, 255, 0.03) 0%, transparent 100%);
    }

    .analysis-page .chart-card .card-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .analysis-page .chart-card .card-title::before {
        content: '';
        width: 4px;
        height: 16px;
        background: linear-gradient(180deg, var(--primary-color, #3370ff), #5b8def);
        border-radius: 2px;
    }

    .analysis-page .chart-container {
        height: 220px;
        width: 100%;
    }

    /* ========================================
       候选人卡片 - 核心优化区域
    ======================================== */
    .analysis-page .candidates-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: var(--radius-lg, 12px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        border: 1px solid var(--border-color, #e5e7eb);
    }

    .analysis-page .candidates-card .card-header {
        background: linear-gradient(90deg, rgba(51, 112, 255, 0.05) 0%, transparent 100%);
        border-bottom: 1px solid rgba(51, 112, 255, 0.1);
    }

    .analysis-page .candidates-card .card-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 17px;
    }

    .analysis-page .candidates-card .card-title svg {
        color: var(--primary-color, #3370ff);
    }

    .analysis-page .sort-controls {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .analysis-page .sort-controls .form-label {
        margin: 0;
        font-size: 13px;
        color: var(--text-secondary);
    }

    .analysis-page .sort-select {
        min-width: 120px;
        padding: 6px 12px;
        font-size: 13px;
    }

    .analysis-page .candidates-list {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 4px 0;
    }

    .analysis-page .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--text-secondary);
        font-size: 14px;
    }

    /* 候选人卡片 - 增强视觉效果 */
    .analysis-page .candidate-card {
        display: flex;
        align-items: center;
        gap: 18px;
        padding: 20px;
        background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
        border-radius: var(--radius-md, 10px);
        border: 1px solid var(--border-color, #e5e7eb);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .analysis-page .candidate-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary-color, #3370ff), #5b8def);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .analysis-page .candidate-card:hover {
        border-color: var(--primary-color, #3370ff);
        box-shadow: 0 8px 24px rgba(51, 112, 255, 0.12);
        transform: translateX(4px);
    }

    .analysis-page .candidate-card:hover::before {
        opacity: 1;
    }

    /* 排名徽章 - 前三名特殊样式 */
    .analysis-page .candidate-rank {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
        color: #fff;
        border-radius: 50%;
        font-size: 15px;
        font-weight: 700;
        flex-shrink: 0;
        box-shadow: 0 4px 10px rgba(100, 116, 139, 0.3);
        position: relative;
    }

    /* 第一名 - 金色 */
    .analysis-page .candidate-card:nth-child(1) .candidate-rank {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4);
    }

    .analysis-page .candidate-card:nth-child(1) .candidate-rank::after {
        content: '👑';
        position: absolute;
        top: -8px;
        font-size: 16px;
    }

    /* 第二名 - 银色 */
    .analysis-page .candidate-card:nth-child(2) .candidate-rank {
        background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
        box-shadow: 0 4px 14px rgba(148, 163, 184, 0.4);
    }

    /* 第三名 - 铜色 */
    .analysis-page .candidate-card:nth-child(3) .candidate-rank {
        background: linear-gradient(135deg, #fb923c 0%, #ea580c 100%);
        box-shadow: 0 4px 14px rgba(234, 88, 12, 0.4);
    }

    .analysis-page .candidate-info {
        flex: 1;
        min-width: 0;
    }

    .analysis-page .candidate-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }

    .analysis-page .candidate-name {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        transition: color 0.2s ease;
    }

    .analysis-page .candidate-card:hover .candidate-name {
        color: var(--primary-color, #3370ff);
    }

    .analysis-page .candidate-education {
        font-size: 13px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        background: rgba(51, 112, 255, 0.08);
    }

    .analysis-page .candidate-details {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        margin-bottom: 10px;
    }

    .analysis-page .detail-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        color: var(--text-secondary);
        transition: color 0.2s ease;
    }

    .analysis-page .candidate-card:hover .detail-item {
        color: #4b5563;
    }

    .analysis-page .detail-item svg {
        flex-shrink: 0;
        opacity: 0.6;
    }

    /* 技能标签 - 增强样式 */
    .analysis-page .candidate-skills {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .analysis-page .skill-tag {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        background: linear-gradient(135deg, rgba(51, 112, 255, 0.1) 0%, rgba(51, 112, 255, 0.05) 100%);
        color: var(--primary-color, #3370ff);
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
        border: 1px solid rgba(51, 112, 255, 0.15);
        transition: all 0.2s ease;
    }

    .analysis-page .candidate-card:hover .skill-tag {
        background: linear-gradient(135deg, rgba(51, 112, 255, 0.15) 0%, rgba(51, 112, 255, 0.08) 100%);
        border-color: rgba(51, 112, 255, 0.25);
    }

    .analysis-page .skill-more {
        font-size: 12px;
        color: var(--text-secondary);
        padding: 4px 8px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 12px;
    }

    /* 推荐指数 - 增强圆形进度条 */
    .analysis-page .candidate-score {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        flex-shrink: 0;
        padding: 8px;
    }

    .analysis-page .score-circle {
        position: relative;
        width: 64px;
        height: 64px;
    }

    .analysis-page .circular-chart {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
    }

    .analysis-page .circle-bg {
        fill: none;
        stroke: #f3f4f6;
        stroke-width: 4;
    }

    .analysis-page .circle {
        fill: none;
        stroke-width: 4;
        stroke-linecap: round;
        transition: stroke-dasharray 0.5s ease;
    }

    .analysis-page .candidate-score.high .circle {
        stroke: url(#gradient-high);
        stroke: #10b981;
    }

    .analysis-page .candidate-score.medium .circle {
        stroke: #f59e0b;
    }

    .analysis-page .candidate-score.low .circle {
        stroke: #ef4444;
    }

    .analysis-page .score-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 16px;
        font-weight: 700;
        color: var(--text-primary);
    }

    .analysis-page .candidate-score.high .score-text {
        color: #10b981;
    }

    .analysis-page .candidate-score.medium .score-text {
        color: #f59e0b;
    }

    .analysis-page .candidate-score.low .score-text {
        color: #ef4444;
    }

    .analysis-page .score-label {
        font-size: 11px;
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* 操作按钮 */
    .analysis-page .candidate-actions {
        flex-shrink: 0;
    }

    .analysis-page .btn-outline {
        padding: 8px 16px;
        background: transparent;
        border: 1px solid var(--border-color, #e5e7eb);
        color: var(--text-primary);
        border-radius: var(--radius-sm, 6px);
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .analysis-page .btn-outline:hover {
        border-color: var(--primary-color, #3370ff);
        color: var(--primary-color, #3370ff);
        background: rgba(51, 112, 255, 0.05);
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(51, 112, 255, 0.15);
    }

    /* 高亮动画 */
    .analysis-page .candidate-card.highlight {
        animation: highlight-pulse 0.6s ease-in-out 3;
        border-color: var(--primary-color, #3370ff);
        box-shadow: 0 0 0 4px rgba(51, 112, 255, 0.2);
    }

    @keyframes highlight-pulse {
        0%, 100% {
            background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
        }
        50% {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        }
    }

    /* ========================================
       响应式设计
    ======================================== */
    @media (max-width: 1024px) {
        .analysis-page .charts-row {
            grid-template-columns: 1fr;
        }

        .analysis-page .conclusion-content h1 {
            font-size: 22px;
        }

        .analysis-page .conclusion-content h2 {
            font-size: 18px;
        }
    }

    @media (max-width: 768px) {
        .analysis-page .metrics-row {
            grid-template-columns: 1fr;
        }

        .analysis-page .query-actions {
            flex-direction: column;
            align-items: stretch;
        }

        .analysis-page .query-actions .form-group {
            min-width: auto;
        }

        .analysis-page .candidate-card {
            flex-wrap: wrap;
            padding: 16px;
        }

        .analysis-page .candidate-score {
            width: 100%;
            flex-direction: row;
            justify-content: flex-start;
            gap: 12px;
            margin-top: 12px;
            padding: 12px;
            background: rgba(0, 0, 0, 0.02);
            border-radius: 8px;
        }

        .analysis-page .candidate-actions {
            width: 100%;
            margin-top: 12px;
        }

        .analysis-page .candidate-actions .btn-outline {
            width: 100%;
        }

        .analysis-page .conclusion-content h1 {
            font-size: 20px;
        }

        .analysis-page .conclusion-content h2 {
            font-size: 17px;
        }

        .analysis-page .conclusion-content table {
            font-size: 13px;
        }

        .analysis-page .conclusion-content th,
        .analysis-page .conclusion-content td {
            padding: 10px 14px;
        }
    }
`;
    document.head.appendChild(analysisStyles);
}

document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'analysis') {
        AnalysisPage.initEvents();
    }
});

window.AnalysisPage = AnalysisPage;
