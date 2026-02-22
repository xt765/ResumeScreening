/**
 * 数据分析模块
 * 提供 RAG 智能查询、统计分析、候选人列表展示功能
 * 使用 ECharts 进行数据可视化
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
                            <span class="result-meta" id="resultMeta"></span>
                        </div>
                        <div class="card-body">
                            <div class="conclusion-content" id="conclusionContent"></div>
                        </div>
                    </div>

                    <!-- 查询结果统计仪表板 -->
                    <div class="analytics-dashboard">
                        <!-- 核心指标卡片 -->
                        <div class="metrics-row">
                            <div class="metric-card">
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
                            <div class="metric-card">
                                <div class="metric-icon success">
                                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                        <polyline points="22 4 12 14.01 9 11.01"/>
                                    </svg>
                                </div>
                                <div class="metric-info">
                                    <div class="metric-value" id="avgSimilarity">0%</div>
                                    <div class="metric-label">平均相似度</div>
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
                            <div class="sort-controls">
                                <label class="form-label">排序方式：</label>
                                <select class="form-control sort-select" id="sortSelect">
                                    <option value="similarity">相似度优先</option>
                                    <option value="work_years">经验优先</option>
                                    <option value="education">学历优先</option>
                                </select>
                            </div>
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

        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.sortCandidates());
        }
    },

    /**
     * 执行查询
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
            UI.showLoading();
            const response = await analysisApi.queryWithAnalytics(query, topK);

            if (response.success) {
                this.queryResults = response.data;
                this.showResults();
                UI.toast(`分析完成，耗时 ${response.data.elapsed_time_ms}ms`, 'success');
            }
        } catch (error) {
            console.error('查询失败:', error);
            UI.toast(error.message || '查询失败', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    /**
     * 显示查询结果
     */
    showResults() {
        const resultsSection = document.getElementById('resultsSection');
        if (!resultsSection || !this.queryResults) return;

        resultsSection.style.display = 'block';

        const data = this.queryResults;
        
        // 更新元信息
        const resultMeta = document.getElementById('resultMeta');
        if (resultMeta) {
            resultMeta.textContent = `耗时 ${data.elapsed_time_ms}ms · 查询ID: ${data.query_id?.substring(0, 8) || '-'}`;
        }

        // 渲染分析结论
        this.renderConclusion(data.answer);

        // 渲染统计数据
        this.renderAnalytics(data.analytics);

        // 渲染候选人列表
        this.renderCandidates(data.sources);

        // 滚动到结果区域
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    /**
     * 渲染分析结论
     * @param {string} answer - LLM生成的分析结论
     */
    renderConclusion(answer) {
        const container = document.getElementById('conclusionContent');
        if (!container) return;

        if (!answer) {
            container.innerHTML = '<div class="text-muted">暂无分析结论</div>';
            return;
        }

        // Markdown 格式化
        let formatted = answer
            .replace(/###\s*(.+)/g, '<h5 class="conclusion-section">$1</h5>')
            .replace(/##\s*(.+)/g, '<h4 class="conclusion-heading">$1</h4>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/\[候选人(\d+)\]/g, '<span class="candidate-ref">[候选人$1]</span>');

        container.innerHTML = `<p>${formatted}</p>`;
    },

    /**
     * 渲染统计数据
     * @param {Object} analytics - 统计数据
     */
    renderAnalytics(analytics) {
        if (!analytics) return;

        // 更新核心指标
        const totalCount = document.getElementById('totalCount');
        const avgSimilarity = document.getElementById('avgSimilarity');

        if (totalCount) {
            totalCount.textContent = analytics.total_count || 0;
        }
        if (avgSimilarity) {
            avgSimilarity.textContent = analytics.avg_similarity 
                ? `${(analytics.avg_similarity * 100).toFixed(1)}%` 
                : '0%';
        }

        // 渲染图表
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

        // 按学历等级排序
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

        // 取前10个
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

        // 取前5个
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

        container.innerHTML = sources.map((source, index) => {
            const metadata = source.metadata || {};
            const similarity = source.similarity_score 
                ? source.similarity_score 
                : (source.distance ? 1 - source.distance : 0);
            const similarityPercent = (similarity * 100).toFixed(1);
            const similarityClass = this.getSimilarityClass(similarity);

            return `
                <div class="candidate-card" data-id="${source.id}">
                    <div class="candidate-rank">${index + 1}</div>
                    <div class="candidate-info">
                        <div class="candidate-header">
                            <span class="candidate-name">${this.escapeHtml(metadata.name || '未知')}</span>
                            <span class="candidate-education" style="color: ${this.educationColors[this.getEducationLabel(metadata.education_level)] || '#374151'}">
                                ${this.getEducationLabel(metadata.education_level) || '-'}
                            </span>
                        </div>
                        <div class="candidate-details">
                            ${metadata.school ? `<span class="detail-item"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>${this.escapeHtml(metadata.school)}</span>` : ''}
                            ${metadata.work_years !== undefined ? `<span class="detail-item"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>${metadata.work_years}年经验</span>` : ''}
                            ${metadata.position ? `<span class="detail-item"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>${this.escapeHtml(metadata.position)}</span>` : ''}
                        </div>
                        ${metadata.skills && metadata.skills.length > 0 ? `
                            <div class="candidate-skills">
                                ${metadata.skills.slice(0, 5).map(skill => `<span class="skill-tag">${this.escapeHtml(skill)}</span>`).join('')}
                                ${metadata.skills.length > 5 ? `<span class="skill-more">+${metadata.skills.length - 5}</span>` : ''}
                            </div>
                        ` : ''}
                    </div>
                    <div class="candidate-score ${similarityClass}">
                        <div class="score-circle">
                            <svg viewBox="0 0 36 36" class="circular-chart">
                                <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                                <path class="circle" stroke-dasharray="${similarityPercent}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            </svg>
                            <span class="score-text">${similarityPercent}%</span>
                        </div>
                        <span class="score-label">相似度</span>
                    </div>
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
     * 排序候选人
     */
    sortCandidates() {
        if (!this.queryResults || !this.queryResults.sources) return;

        const sortSelect = document.getElementById('sortSelect');
        const sortBy = sortSelect?.value || 'similarity';

        const sources = [...this.queryResults.sources];

        sources.sort((a, b) => {
            const metaA = a.metadata || {};
            const metaB = b.metadata || {};

            switch (sortBy) {
                case 'similarity': {
                    const scoreA = a.similarity_score || (a.distance ? 1 - a.distance : 0);
                    const scoreB = b.similarity_score || (b.distance ? 1 - b.distance : 0);
                    return scoreB - scoreA;
                }
                case 'work_years': {
                    return (metaB.work_years || 0) - (metaA.work_years || 0);
                }
                case 'education': {
                    const eduOrder = { 'doctor': 5, 'master': 4, 'bachelor': 3, 'college': 2, 'high_school': 1 };
                    return (eduOrder[metaB.education_level] || 0) - (eduOrder[metaA.education_level] || 0);
                }
                default:
                    return 0;
            }
        });

        this.renderCandidates(sources);
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

    /**
     * 查看人才详情
     * @param {string} talentId - 人才ID
     */
    viewTalentDetail(talentId) {
        window.location.hash = `/talents?id=${talentId}`;
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
        this.queryResults = null;
    }
};

// 注入样式
if (!document.getElementById('analysis-styles')) {
    const analysisStyles = document.createElement('style');
    analysisStyles.id = 'analysis-styles';
    analysisStyles.textContent = `
    /* 页面标题 */
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

    /* 查询区域 */
    .analysis-page .query-section {
        margin-bottom: 24px;
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
        min-width: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }

    /* 分析结论卡片 */
    .analysis-page .conclusion-card {
        margin-bottom: 24px;
        border-left: 4px solid var(--primary-color, #3b82f6);
    }

    .analysis-page .result-meta {
        font-size: 13px;
        color: var(--text-secondary);
    }

    .analysis-page .conclusion-content {
        font-size: 14px;
        line-height: 1.8;
        color: var(--text-primary);
    }

    .analysis-page .conclusion-content p {
        margin-bottom: 12px;
    }

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

    .analysis-page .candidate-ref {
        background: #dbeafe;
        color: #1e40af;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }

    /* 统计仪表板 */
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
        padding: 20px;
        background: #fff;
        border-radius: var(--radius-lg, 12px);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .analysis-page .metric-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 12px;
    }

    .analysis-page .metric-icon.primary {
        background: #eff6ff;
        color: #3b82f6;
    }

    .analysis-page .metric-icon.success {
        background: #ecfdf5;
        color: #10b981;
    }

    .analysis-page .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
    }

    .analysis-page .metric-label {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 4px;
    }

    /* 图表区域 */
    .analysis-page .charts-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 16px;
    }

    .analysis-page .chart-card {
        background: #fff;
        border-radius: var(--radius-lg, 12px);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .analysis-page .chart-card .card-header {
        padding: 16px 20px;
        border-bottom: 1px solid var(--border-color, #e5e7eb);
    }

    .analysis-page .chart-card .card-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .analysis-page .chart-container {
        height: 200px;
        width: 100%;
    }

    /* 候选人列表 */
    .analysis-page .candidates-card {
        background: #fff;
        border-radius: var(--radius-lg, 12px);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
        gap: 12px;
    }

    .analysis-page .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: var(--text-secondary);
        font-size: 14px;
    }

    /* 候选人卡片 */
    .analysis-page .candidate-card {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background: var(--bg-secondary, #f9fafb);
        border-radius: var(--radius-md, 8px);
        border: 1px solid var(--border-color, #e5e7eb);
        transition: all 0.2s;
    }

    .analysis-page .candidate-card:hover {
        border-color: var(--primary-color, #3b82f6);
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
    }

    .analysis-page .candidate-rank {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background: var(--primary-color, #3b82f6);
        color: #fff;
        border-radius: 50%;
        font-size: 14px;
        font-weight: 600;
        flex-shrink: 0;
    }

    .analysis-page .candidate-info {
        flex: 1;
        min-width: 0;
    }

    .analysis-page .candidate-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }

    .analysis-page .candidate-name {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
    }

    .analysis-page .candidate-education {
        font-size: 13px;
        font-weight: 500;
    }

    .analysis-page .candidate-details {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 8px;
    }

    .analysis-page .detail-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        color: var(--text-secondary);
    }

    .analysis-page .detail-item svg {
        flex-shrink: 0;
    }

    .analysis-page .candidate-skills {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .analysis-page .skill-tag {
        display: inline-block;
        padding: 2px 8px;
        background: #eff6ff;
        color: #3b82f6;
        border-radius: 4px;
        font-size: 12px;
    }

    .analysis-page .skill-more {
        font-size: 12px;
        color: var(--text-secondary);
    }

    /* 相似度分数 */
    .analysis-page .candidate-score {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        flex-shrink: 0;
    }

    .analysis-page .score-circle {
        position: relative;
        width: 56px;
        height: 56px;
    }

    .analysis-page .circular-chart {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
    }

    .analysis-page .circle-bg {
        fill: none;
        stroke: #e5e7eb;
        stroke-width: 3;
    }

    .analysis-page .circle {
        fill: none;
        stroke-width: 3;
        stroke-linecap: round;
        transition: stroke-dasharray 0.3s ease;
    }

    .analysis-page .candidate-score.high .circle {
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
        font-size: 12px;
        font-weight: 600;
        color: var(--text-primary);
    }

    .analysis-page .score-label {
        font-size: 11px;
        color: var(--text-secondary);
    }

    .analysis-page .candidate-actions {
        flex-shrink: 0;
    }

    .analysis-page .btn-outline {
        padding: 6px 12px;
        background: transparent;
        border: 1px solid var(--border-color, #e5e7eb);
        color: var(--text-primary);
        border-radius: var(--radius-sm, 6px);
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .analysis-page .btn-outline:hover {
        border-color: var(--primary-color, #3b82f6);
        color: var(--primary-color, #3b82f6);
    }

    /* 响应式布局 */
    @media (max-width: 1024px) {
        .analysis-page .charts-row {
            grid-template-columns: 1fr;
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
        }

        .analysis-page .candidate-score {
            width: 100%;
            flex-direction: row;
            justify-content: flex-start;
            gap: 12px;
            margin-top: 12px;
        }

        .analysis-page .candidate-actions {
            width: 100%;
            margin-top: 12px;
        }

        .analysis-page .candidate-actions .btn-outline {
            width: 100%;
        }
    }
`;
    document.head.appendChild(analysisStyles);
}

// 页面加载完成后初始化事件
document.addEventListener('DOMContentLoaded', () => {
    if (AppState.currentPage === 'analysis') {
        AnalysisPage.initEvents();
    }
});

// 导出到全局
window.AnalysisPage = AnalysisPage;
