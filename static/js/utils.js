/**
 * MVP前端优化 - 统一工具函数库
 * 提供统一的API调用、错误处理、UI更新等功能
 */

/**
 * 统一API调用函数
 * @param {string} endpoint - API端点（会自动添加/api前缀）
 * @param {object} options - 请求选项 {method, body, headers}
 * @returns {Promise<object>} API响应数据
 */
async function apiCall(endpoint, options = {}) {
    // 确保endpoint以/开头
    if (!endpoint.startsWith('/')) {
        endpoint = '/' + endpoint;
    }
    
    // 如果endpoint不包含/api，自动添加
    if (!endpoint.startsWith('/api')) {
        endpoint = '/api' + endpoint;
    }
    
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    // 合并选项
    const requestOptions = {
        ...defaultOptions,
        ...options
    };
    
    // 如果body是对象，自动序列化为JSON
    if (requestOptions.body && typeof requestOptions.body === 'object') {
        requestOptions.body = JSON.stringify(requestOptions.body);
    }
    
    try {
        const response = await fetch(endpoint, requestOptions);
        const data = await response.json();
        
        // 检查响应是否成功
        if (!response.ok || !data.success) {
            const errorMessage = data.error || `请求失败 (${response.status})`;
            throw new Error(errorMessage);
        }
        
        return data;
    } catch (error) {
        // 如果是网络错误或其他错误，包装为统一格式
        if (error.message) {
            throw error;
        }
        throw new Error(`网络错误: ${error.message || '未知错误'}`);
    }
}

/**
 * 显示错误信息
 * @param {HTMLElement|string} element - 目标元素或元素ID
 * @param {string} message - 错误消息
 */
function showError(element, message) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (!el) {
        console.error('showError: 元素不存在', element);
        return;
    }
    el.innerHTML = `<div class="error">❌ ${escapeHtml(message)}</div>`;
}

/**
 * 显示成功信息
 * @param {HTMLElement|string} element - 目标元素或元素ID
 * @param {string} message - 成功消息
 */
function showSuccess(element, message) {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (!el) {
        console.error('showSuccess: 元素不存在', element);
        return;
    }
    el.innerHTML = `<div class="success">✅ ${escapeHtml(message)}</div>`;
}

/**
 * 显示加载状态
 * @param {HTMLElement|string} element - 目标元素或元素ID
 * @param {string} message - 加载消息
 */
function showLoading(element, message = '加载中...') {
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (!el) {
        console.error('showLoading: 元素不存在', element);
        return;
    }
    el.innerHTML = `<div class="loading">${escapeHtml(message)}</div>`;
}

/**
 * HTML转义函数，防止XSS攻击
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的HTML安全文本
 */
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 统一列表项选择功能
 * @param {string} containerId - 容器元素ID
 * @param {string} itemId - 要选中的项目ID
 * @param {string} selectedClass - 选中状态的CSS类名，默认为'selected'
 */
function selectListItem(containerId, itemId, selectedClass = 'selected') {
    // 移除所有选中状态
    const container = document.getElementById(containerId);
    if (container) {
        container.querySelectorAll('.list-item').forEach(item => {
            item.classList.remove(selectedClass);
        });
    }
    
    // 添加选中状态
    const selectedItem = document.getElementById(itemId);
    if (selectedItem) {
        selectedItem.classList.add(selectedClass);
    }
}
