document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const statsInfo = document.getElementById('statsInfo');
    
    // 初始化
    loadStats();
    
    // 搜索按钮点击事件
    searchBtn.addEventListener('click', performSearch);
    
    // 回车键搜索
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // 执行搜索
    function performSearch() {
        const query = searchInput.value.trim();
        
        if (!query) {
            showResult('请输入要查询的职业名称', 'error');
            return;
        }
        
        // 显示加载状态
        showLoading(true);
        hideResult();
        searchBtn.disabled = true;
        
        // 发送搜索请求
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            searchBtn.disabled = false;
            
            if (data.success) {
                showSuccessResult(data);
            } else {
                showErrorResult(data);
            }
        })
        .catch(error => {
            showLoading(false);
            searchBtn.disabled = false;
            console.error('搜索错误:', error);
            showResult('网络错误，请稍后重试', 'error');
        });
    }
    
    // 显示成功结果
    function showSuccessResult(data) {
        let html = `<div class="main-message">${data.message}</div>`;
        
        if (data.data) {
            html += '<div class="match-info">';
            
            if (data.data.match_type === 'exact') {
                html += '<strong>✓ 精确匹配</strong>';
            } else if (data.data.match_type === 'fuzzy') {
                html += `<strong>~ 模糊匹配</strong>`;
            }
            
            if (data.data.has_aliases) {
                html += '<br>该职业存在别称';
            }
            
            // 根据状态显示不同的样式类
            const statusClass = getStatusClass(data.data.status);
            html += `<br><span class="status-badge ${statusClass}">状态: ${data.data.chinese_status}</span>`;
            
            html += '</div>';
        }
        
        showResult(html, 'success');
    }
    
    // 根据状态获取CSS类名
    function getStatusClass(status) {
        const statusMap = {
            'Occupied': 'status-occupied',
            'Hold': 'status-hold',
            'Available': 'status-available'
        };
        return statusMap[status] || 'status-unknown';
    }
    
    // 显示错误结果
    function showErrorResult(data) {
        let html = `<div class="main-message">${data.message}</div>`;
        
        if (data.suggestions && data.suggestions.length > 0) {
            html += `
                <div class="suggestions">
                    <h4>您可能想查询：</h4>
                    <div class="suggestion-list">
                        ${data.suggestions.map(suggestion => 
                            `<span class="suggestion-item" onclick="searchSuggestion('${suggestion}')">${suggestion}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
            showResult(html, 'suggestions');
        } else {
            showResult(html, 'error');
        }
    }
    
    // 点击建议词搜索
    window.searchSuggestion = function(suggestion) {
        searchInput.value = suggestion;
        performSearch();
    };
    
    // 显示结果
    function showResult(message, type) {
        result.innerHTML = message;
        result.className = `result ${type}`;
        result.classList.remove('hidden');
    }
    
    // 隐藏结果
    function hideResult() {
        result.classList.add('hidden');
    }
    
    // 显示/隐藏加载状态
    function showLoading(show) {
        if (show) {
            loading.classList.remove('hidden');
        } else {
            loading.classList.add('hidden');
        }
    }
    
    // 加载统计信息
    function loadStats() {
        fetch('/stats')
        .then(response => response.json())
        .then(data => {
            const source = data.data_source === 'online' ? '在线表格' : '本地Excel文件';
            statsInfo.textContent = `已加载 ${data.total_occupations} 个才能，数据源：${source}`;
        })
        .catch(error => {
            console.error('加载统计信息失败:', error);
            statsInfo.textContent = '数据加载中...';
        });
    }
    
    // 输入框获得焦点时清空结果
    searchInput.addEventListener('focus', function() {
        if (result.classList.contains('error') || result.classList.contains('suggestions')) {
            hideResult();
        }
    });

    // 每2分钟自动刷新数据
    setInterval(() => {
        fetch('/reload', {method: 'POST'})
        .then(() => loadStats());
    }, 2 * 60 * 1000);

});