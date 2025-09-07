// 原有的缩放和页面控制功能
function fitPageToWindow() {
  const page = document.querySelector('.page');
  const container = document.querySelector('.page-wrapper');

  if (!page) return;

  const windowWidth = window.innerWidth;
  const windowHeight = window.innerHeight;

  const scaleX = windowWidth / page.offsetWidth;
  const scaleY = windowHeight / page.offsetHeight;

  const scale = Math.min(scaleX, scaleY, 1);

  page.style.transform = `scale(${scale})`;
  page.dataset.scale = scale;
}

function setupZoomControl() {
  const scaleInput = document.getElementById("scale-range");
  const pages = document.querySelectorAll(".page");

  scaleInput.addEventListener("input", () => {
    const factor = scaleInput.value;

    pages.forEach(page => {
      const base = parseFloat(page.dataset.scale || 1);
      const newScale = base * factor;
      page.style.transform = `scale(${newScale})`;
    });
  });
}

// 多页面缩放控制
function setupMultiPageZoom() {
  const scaleInput = document.getElementById("scale-range");
  const pages = document.querySelectorAll(".page");

  // 为所有页面设置基础缩放数据
  const windowWidth = window.innerWidth - 260; // 减去控制面板宽度
  const windowHeight = window.innerHeight;

  pages.forEach(page => {
    const scaleX = windowWidth / page.offsetWidth;
    const scaleY = windowHeight / page.offsetHeight;
    const scale = Math.min(scaleX, scaleY, 1);
    page.dataset.scale = scale;
    page.style.transform = `scale(${scale})`;
  });

  // 重新绑定缩放控制
  const newHandler = () => {
    const factor = scaleInput.value;
    pages.forEach(page => {
      const base = parseFloat(page.dataset.scale || 1);
      const newScale = base * factor;
      page.style.transform = `scale(${newScale})`;
    });
  };

  // 移除旧的事件监听器，添加新的
  scaleInput.removeEventListener("input", newHandler);
  scaleInput.addEventListener("input", newHandler);
}

function setupControls() {
  const identifierInput = document.getElementById("identifier-input");
  const startPageInput = document.getElementById("start-page-input");

  // 添加应用按钮功能
  document.getElementById("apply-settings").addEventListener("click", () => {
    const newId = identifierInput.value.trim();
    const newStartPage = startPageInput.value.trim();

    // 更新所有页面的标识符
    const identifiers = document.querySelectorAll(".identifier");
    identifiers.forEach(el => {
      if (newId) el.textContent = newId;
    });

    // 更新所有页面的页码
    const pageNumbers = document.querySelectorAll(".page-number");
    pageNumbers.forEach((el, index) => {
      if (newStartPage) {
        const pageNum = parseInt(newStartPage) + index;
        el.textContent = pageNum.toString().padStart(2, '0');
      }
    });
  });
}

// 新增的排版工具功能
class LayoutGenerator {
  constructor() {
    this.data = [];
    this.currentFile = null;
    this.startPageNumber = 2;
    this.identifier = 'DP-01';
    this.isGenerated = false;
    this.init();
  }

  init() {
    this.setupDataImport();
    this.setupExport();
    this.setupSettings();
  }

  setupDataImport() {
    // 文件输入
    document.getElementById('file-input').addEventListener('change', (e) => {
      this.handleFileInput(e);
    });

    // 编码重读
    document.getElementById('reread-csv').addEventListener('click', () => {
      if (this.currentFile) {
        const encoding = document.getElementById('encoding-select').value;
        this.readCSVWithEncoding(this.currentFile, encoding);
      }
    });

    // Google Sheets
    document.getElementById('load-sheets').addEventListener('click', () => {
      this.loadGoogleSheets();
    });

    // 生成排版
    document.getElementById('generate-layout').addEventListener('click', () => {
      this.generateLayout();
    });
  }

  setupExport() {
    document.getElementById('export-png').addEventListener('click', () => {
      this.exportToPNG();
    });
  }

  setupSettings() {
    // 应用设置按钮
    document.getElementById('apply-settings').addEventListener('click', () => {
      if (this.isGenerated) {
        this.applySettings();
      }
    });
  }

  applySettings() {
    const newId = document.getElementById('identifier-input').value.trim();
    const newStartPage = parseInt(document.getElementById('start-page-input').value) || 2;

    if (!newId) {
      alert('请输入编号');
      return;
    }

    this.identifier = newId;
    this.startPageNumber = newStartPage;

    // 更新所有页面
    const pages = document.querySelectorAll('.page');
    pages.forEach((page, pageIndex) => {
      // 更新标识符
      const identifier = page.querySelector('.identifier');
      if (identifier) identifier.textContent = newId;

      // 更新页码
      const pageNumber = page.querySelector('.page-number');
      if (pageNumber) {
        const pageNum = newStartPage + pageIndex;
        pageNumber.textContent = pageNum.toString().padStart(2, '0');
      }
    });
  }

  async handleFileInput(event) {
    const file = event.target.files[0];
    if (!file) return;

    this.currentFile = file;

    try {
      let data;

      if (file.name.toLowerCase().endsWith('.csv')) {
        document.getElementById('encoding-options').style.display = 'block';
        data = await this.readCSVWithEncoding(file, 'utf-8');
      } else {
        document.getElementById('encoding-options').style.display = 'none';
        data = await this.readExcelFile(file);
      }

      this.data = data;
      this.showDataPreview(data);
      document.getElementById('generate-layout').disabled = false;
    } catch (error) {
      alert('文件读取失败: ' + error.message);
      console.error('文件读取错误:', error);
    }
  }

  async readExcelFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const workbook = XLSX.read(e.target.result, {
            type: 'array',
            codepage: 65001
          });

          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const jsonData = XLSX.utils.sheet_to_json(firstSheet, {
            header: 1,
            defval: '',
            raw: false
          });

          console.log('Excel原始数据:', jsonData);

          if (jsonData.length > 1) {
            // 获取A1单元格的编号（如果存在）
            const identifierFromA1 = jsonData[0][0]; // A1单元格
            if (identifierFromA1 && identifierFromA1.trim()) {
              // 更新编号输入框
              document.getElementById('identifier-input').value = identifierFromA1.trim();
              this.identifier = identifierFromA1.trim();
            }

            // 重要修复：只使用列索引，不使用表头名称
            const rows = jsonData.slice(1).map((row, index) => {
              const obj = {};
              // 只使用列字母索引
              row.forEach((cell, colIndex) => {
                const colLetter = String.fromCharCode(65 + colIndex); // A, B, C, D...
                obj[colLetter] = cell || '';
              });
              console.log(`第${index + 1}行数据:`, obj);
              return obj;
            });

            console.log('处理后的数据:', rows);
            resolve(rows);
          } else {
            resolve([]);
          }
        } catch (error) {
          console.error('Excel解析错误:', error);
          reject(error);
        }
      };

      reader.onerror = () => reject(new Error('文件读取错误'));
      reader.readAsArrayBuffer(file);
    });
  }

  async readCSVWithEncoding(file, encoding = 'utf-8') {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          let text;

          if (encoding === 'utf-8') {
            text = e.target.result;
          } else {
            const uint8Array = new Uint8Array(e.target.result);
            text = this.decodeText(uint8Array, encoding);
          }

          const data = this.parseCSV(text);
          this.data = data;
          this.showDataPreview(data);
          resolve(data);
        } catch (error) {
          reject(error);
        }
      };

      reader.onerror = () => reject(new Error('CSV文件读取错误'));

      if (encoding === 'utf-8') {
        reader.readAsText(file, 'utf-8');
      } else {
        reader.readAsArrayBuffer(file);
      }
    });
  }

  decodeText(uint8Array, encoding) {
    try {
      if (typeof TextDecoder !== 'undefined') {
        const decoder = new TextDecoder(encoding === 'gbk' ? 'gb2312' : encoding);
        return decoder.decode(uint8Array);
      }
    } catch (error) {
      console.warn('编码转换失败，使用UTF-8:', error);
    }

    const decoder = new TextDecoder('utf-8');
    return decoder.decode(uint8Array);
  }

  parseCSV(csvText) {
    const lines = csvText.split('\n').filter(line => line.trim());
    if (lines.length < 2) return [];

    const parseCSVLine = (line) => {
      const result = [];
      let current = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim().replace(/^"/, '').replace(/"$/, ''));
          current = '';
        } else {
          current += char;
        }
      }

      result.push(current.trim().replace(/^"/, '').replace(/"$/, ''));
      return result;
    };

    const firstLine = parseCSVLine(lines[0]);
    return lines.slice(1).map(line => {
      const values = parseCSVLine(line);
      const obj = {};
      values.forEach((value, index) => {
        const colLetter = String.fromCharCode(65 + index); // A, B, C, D...
        obj[colLetter] = value || '';
      });
      return obj;
    });
  }

  async loadGoogleSheets() {
    const url = document.getElementById('sheets-url').value.trim();
    if (!url) {
      alert('请输入Google Sheets链接');
      return;
    }

    try {
      let csvUrl;
      if (url.includes('/edit')) {
        csvUrl = url.replace('/edit#gid=', '/export?format=csv&gid=')
                    .replace('/edit', '/export?format=csv');
      } else {
        csvUrl = url + '/export?format=csv';
      }

      const response = await fetch(csvUrl);
      if (!response.ok) throw new Error('无法访问Google Sheets');

      const csvText = await response.text();
      const data = this.parseCSV(csvText);

      this.data = data;
      this.showDataPreview(data);
      document.getElementById('generate-layout').disabled = false;
      document.getElementById('encoding-options').style.display = 'none';

    } catch (error) {
      alert('加载Google Sheets失败: ' + error.message);
    }
  }

  showDataPreview(data) {
    console.log('showDataPreview 调用，data:', data);
    const preview = document.getElementById('data-preview');
    const content = document.getElementById('preview-content');

    if (!preview || !content) {
      console.error('找不到预览元素');
      return;
    }

    if (data.length === 0) {
      content.innerHTML = '无数据';
      preview.style.display = 'block';
      return;
    }

    const headers = Object.keys(data[0]);
    let html = `${data.length}行, 列: ${headers.join(', ')}<br>`;

    data.slice(0, 3).forEach((row, index) => {
      html += `第${index + 1}行: A="${row.A}" B="${row.B}" C="${row.C}" D="${row.D}" E="${row.E}"<br>`;
    });

    content.innerHTML = html;
    preview.style.display = 'block';
  }

  generateLayout() {
    if (this.data.length === 0) {
      alert('请先导入数据');
      return;
    }

    // 获取当前设置
    this.identifier = document.getElementById('identifier-input').value || 'DP-01';
    this.startPageNumber = parseInt(document.getElementById('start-page-input').value) || 2;

    const wrapper = document.querySelector('.page-wrapper');
    wrapper.innerHTML = '';

    const itemsPerPage = 3;
    const totalPages = Math.ceil(this.data.length / itemsPerPage);

    for (let pageIndex = 0; pageIndex < totalPages; pageIndex++) {
      const pageNumber = this.startPageNumber + pageIndex;
      const startIndex = pageIndex * itemsPerPage;
      const endIndex = Math.min(startIndex + itemsPerPage, this.data.length);
      const pageData = this.data.slice(startIndex, endIndex);

      const pageElement = this.createPage(pageNumber, pageData);
      wrapper.appendChild(pageElement);
    }

    // 切换到多页面缩放模式
    setupMultiPageZoom();

    // 标记为已生成
    this.isGenerated = true;

    // 启用相关功能
    document.getElementById('export-png').disabled = false;
  }

  createPage(pageNumber, data) {
    const page = document.createElement('div');
    page.className = 'page';
    page.id = pageNumber === this.startPageNumber ? 'page' : `page-${pageNumber}`;

    // 标识符
    const identifier = document.createElement('div');
    identifier.className = 'identifier';
    identifier.textContent = this.identifier;
    page.appendChild(identifier);

    // 三个box
    for (let i = 0; i < 3; i++) {
      const box = document.createElement('div');
      box.className = 'box';
      box.id = `box${i + 1}`;

      if (data[i]) {
        const content = this.createBoxContent(data[i]);
        box.appendChild(content);
      }

      page.appendChild(box);
    }

    // 页码
    const pageNum = document.createElement('div');
    pageNum.className = 'page-number';
    pageNum.textContent = pageNumber.toString().padStart(2, '0');
    page.appendChild(pageNum);

    return page;
  }

  createBoxContent(rowData) {
    console.log('createBoxContent 调用，rowData:', rowData);

    const content = document.createElement('div');
    content.className = 'event-content';

    // 根据你提供的列信息，重新映射：
    // A: #01（编号）
    // B: 坐标
    // C: 区域
    // D: 事件内容
    // E: 事件类别
    // F: 物资
    // G: 是否有后续剧情
    // H: 事件结算
    // I: 是否完成
    // J: 行动点消耗
    // K: 使用技能
    // L: 判定等级

    const coordinate = rowData['B'] || '';      // 坐标
    const area = rowData['C'] || '';            // 区域
    const description = rowData['D'] || '';     // 事件内容
    const eventType = rowData['E'] || '';       // 事件类别
    const reward = rowData['F'] || '';          // 物资
    const isCompleted = rowData['I'] === '是' || rowData['I'] === 'true' || rowData['I'] === '完成' || rowData['I'] === '1';

    console.log('提取的数据:', {
      coordinate, area, description, eventType, reward, isCompleted
    });

    // 图标类型映射表（6种图标类型）
    const iconMapping = {
      // 中文到英文的映射
      '自然': 'nature',
      '工程': 'engineering',
      '体能': 'physical',
      '社交': 'diplomacy',
      '特殊': 'special',
      '任意': 'wildcard',
      // 英文保持原样
      'nature': 'nature',
      'engineering': 'engineering',
      'physical': 'physical',
      'diplomacy': 'diplomacy',
      'special': 'special',
      'wildcard': 'wildcard'
    };

    // 图标：使用CSS样式类
    if (eventType) {
      const icon = document.createElement('img');
      icon.className = 'event-icon';

      const mappedIconType = iconMapping[eventType] || eventType.toLowerCase();
      icon.src = `./assets/img/task-${mappedIconType}.png`;

      icon.onerror = () => {
        console.warn(`图标文件不存在: task-${mappedIconType}.png`);
        icon.style.display = 'none';
      };

      content.appendChild(icon);
    }

    // 地理位置：使用CSS样式类
    if (coordinate || area) {
      const location = document.createElement('div');
      location.className = 'event-location';
      location.textContent = `${coordinate}${area ? ' - ' + area : ''}`;
      content.appendChild(location);
    }

    // 事件描述：使用CSS样式类
    if (description) {
      const desc = document.createElement('div');
      desc.className = 'event-description';
      desc.textContent = description;
      content.appendChild(desc);
    }

    // 奖励：使用CSS样式类
    const rewardDiv = document.createElement('div');
    rewardDiv.className = 'event-reward';
    rewardDiv.textContent = isCompleted ? `获得物资：${reward}` : '获得物资：？';
    content.appendChild(rewardDiv);

    // 如果已完成，添加遮罩
    if (isCompleted) {
      const mask = document.createElement('div');
      mask.className = 'event-mask';
      content.appendChild(mask);
    }

    return content;
  }

  async exportToPNG() {
    const pages = document.querySelectorAll('.page');
    if (pages.length === 0) {
      alert('没有页面可导出');
      return;
    }

    const statusDiv = document.getElementById('export-status');
    statusDiv.style.display = 'block';
    statusDiv.textContent = '正在导出...';

    try {
      for (let i = 0; i < pages.length; i++) {
        const page = pages[i];
        const pageNum = this.startPageNumber + i;

        statusDiv.textContent = `导出 ${i + 1}/${pages.length}...`;

        const originalTransform = page.style.transform;
        page.style.transform = 'scale(1)';

        const canvas = await html2canvas(page, {
          width: 1230,
          height: 1729,
          scale: 2,
          useCORS: true,
          backgroundColor: '#ffffff'
        });

        page.style.transform = originalTransform;

        const link = document.createElement('a');
        link.download = `${this.identifier}-${pageNum.toString().padStart(2, '0')}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();

        await new Promise(resolve => setTimeout(resolve, 500));
      }

      statusDiv.textContent = `导出完成！`;
      setTimeout(() => statusDiv.style.display = 'none', 3000);

    } catch (error) {
      statusDiv.textContent = '导出失败: ' + error.message;
      console.error('Export error:', error);
    }
  }
}

// Initialize
window.addEventListener('load', () => {
  fitPageToWindow();
  setupZoomControl();
  setupControls();

  // 初始化排版工具
  new LayoutGenerator();
});

window.addEventListener('resize', fitPageToWindow);