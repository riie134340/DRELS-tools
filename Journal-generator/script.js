// ===== 统一缩放控制 =====
const viewerEl = document.getElementById('viewer');     // .page-wrapper
const pagesEl  = document.getElementById('pages');       // 多页容器
const scaleInput = document.getElementById('scale-range');

function setScale(v) {
  viewerEl.style.setProperty('--scale', v);
  if (scaleInput) scaleInput.value = String(v);
}

function getControlsWidth() {
  const controls = document.querySelector('.controls');
  return controls ? controls.offsetWidth : 0;
}

function getFirstPageSize() {
  const first = pagesEl?.querySelector('.page');
  return first ? { w: first.offsetWidth, h: first.offsetHeight } : { w: 1230, h: 1729 };
}

function computeAutoScale(isMulti) {
  const { w: pageW, h: pageH } = getFirstPageSize();
  const usableW = window.innerWidth - getControlsWidth() - 24 * 2;
  const scaleByW = Math.max(Math.min(usableW / pageW, 1), 0.1);
  if (!isMulti) {
    const usableH = window.innerHeight - 24 * 2;
    const scaleByH = Math.max(Math.min(usableH / pageH, 1), 0.1);
    return Math.min(scaleByW, scaleByH);
  }
  return scaleByW;
}

function applyAutoScale() {
  const isMulti = viewerEl.classList.contains('pdf-preview');
  setScale(computeAutoScale(isMulti));
}

function setupUnifiedZoomControl() {
  if (!scaleInput) return;
  scaleInput.addEventListener('input', (e) => {
    const v = parseFloat(e.target.value);
    if (Number.isFinite(v)) setScale(v);
  });
}

function setMode(isMulti) {
  viewerEl.classList.toggle('pdf-preview', isMulti); // 多页模式
  viewerEl.classList.toggle('single', !isMulti);      // 单页模式
  viewerEl.querySelectorAll('.page').forEach(p => { p.style.transform = ''; p.dataset.scale = ''; });
  applyAutoScale();
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
    const raw = document.getElementById('sheets-url').value.trim();
    if (!raw) return alert('请输入 Google Sheets 链接');

    try {
      const { id, gid, sheetName } = parseSheetsUrl(raw);
      // 优先用 gid，若提供了 sheetName 则用 gviz by name
      const csvUrl = sheetName
      ? `https://docs.google.com/spreadsheets/d/${id}/gviz/tq?tqx=out:csv&sheet=${encodeURIComponent(sheetName)}`
      : `https://docs.google.com/spreadsheets/d/${id}/export?format=csv&gid=${gid}`;

      const res = await fetch(csvUrl, { credentials: 'omit' });
      if (!res.ok) throw new Error(`无法访问 CSV（${res.status}）`);

      const text = await res.text();

      // 如果拿到的是 HTML（多半是未公开或复制了 Drive 链接），给出提示
      if (/<!doctype html>|<html/i.test(text)) {
        throw new Error('返回的不是 CSV 内容，可能权限未公开，或链接不是 docs.google.com/spreadsheets。');
      }

      const data = this.parseCSV(text);
      this.data = data;
      this.showDataPreview(data);

      document.getElementById('generate-layout').disabled = false;
      document.getElementById('encoding-options').style.display = 'none';
    } catch (err) {
      console.error(err);
      alert(
        '加载 Google Sheets 失败：' + err.message +
        '\n\n请检查：\n1) 链接是否为 docs.google.com/spreadsheets/d/... \n2) 分享权限是否为“Anyone with the link（查看者）”\n3) 如需非首个工作表，请复制含 #gid=... 的链接或在链接末尾加 ?sheet=工作表名'
      );
    }

    function parseSheetsUrl(input) {
      // 允许用户随便粘贴，尽量宽松解析
      const m = String(input).match(/https:\/\/docs\.google\.com\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
      if (!m) throw new Error('不是有效的 Google Sheets 链接（需要 docs.google.com/spreadsheets/d/...）');
      const id = m[1];

      // 优先从 #gid= 里取，没有就用 0
      const hashGid = String(input).match(/[#?&]gid=(\d+)/);
      const gid = hashGid ? hashGid[1] : '0';

      // 可选：支持在链接最后手动加 ?sheet=表名 来按表名导出
      const sheetMatch = String(input).match(/[?&]sheet=([^&#]+)/i);
      const sheetName = sheetMatch ? decodeURIComponent(sheetMatch[1]) : '';

      return { id, gid, sheetName };
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

    // 读取当前设置
    this.identifier = document.getElementById('identifier-input').value || 'DP-01';
    this.startPageNumber = parseInt(document.getElementById('start-page-input').value) || 2;

    const pagesContainer = document.getElementById('pages');
    if (!pagesContainer) {
      alert('找不到 #pages 容器');
      return;
    }

    // 1) 取首屏模板(包含 .box 的结构)
    const templatePage = pagesContainer.querySelector('.page');
    if (!templatePage) {
      alert('首屏模板 .page 不存在');
      return;
    }
    const pageTemplate = templatePage.cloneNode(true); // 深度克隆

    // 2) 清空容器(模板已在内存)
    pagesContainer.innerHTML = '';

    // 3) 展开数据:如果已完成(I列为"是")且G列为"是",插入后续剧情
    const expandedData = [];
    this.data.forEach(row => {
      expandedData.push(row);

      // 检查是否有后续剧情:必须同时满足 I列为"是"(已完成) 和 G列为"是"(有后续)
      const isCompleted = row['I'] === '是' || row['I'] === 'true' || row['I'] === '完成' || row['I'] === '1';
      const hasFollow = row['G'] === '是' || row['G'] === 'true' || row['G'] === '1';

      if (isCompleted && hasFollow && row['H']) {
        // 创建后续剧情事件(使用H列内容)
        const followUpEvent = {
          A: row['A'], // 保持相同编号
          B: row['B'], // 保持相同坐标
          C: row['C'], // 保持相同区域
          D: row['H'], // 后续剧情内容来自H列
          E: row['E'], // 保持相同事件类型
          F: '-',       // 物资固定为空
          G: '否',     // 是否有后续固定为否
          H: '',       // 无后续
          I: '否', // 保持完成状态
          J: row['J'], // 行动点消耗
          K: row['K'], // 使用技能
          L: row['L']  // 判定等级
        };
        expandedData.push(followUpEvent);
      }
    });

    console.log('展开后的数据:', expandedData);

    // 4) 每页 3 条数据
    const itemsPerPage = 3;
    const totalPages = Math.ceil(expandedData.length / itemsPerPage);

    for (let pageIndex = 0; pageIndex < totalPages; pageIndex++) {
      const pageNumber = this.startPageNumber + pageIndex;
      const startIndex = pageIndex * itemsPerPage;
      const endIndex = Math.min(startIndex + itemsPerPage, expandedData.length);
      const pageData = expandedData.slice(startIndex, endIndex);

      const page = this.buildPageFromTemplate(pageTemplate, pageNumber, pageData);
      pagesContainer.appendChild(page);
    }

    setMode(true);            // 切到多页
    this.isGenerated = true;
    document.getElementById('export-png').disabled = false;
  }

  buildPageFromTemplate(template, pageNumber, pageData) {
    const page = template.cloneNode(true);

    // 避免重复 id
    page.id = `page-${String(pageNumber).padStart(2, '0')}`;

    // 标识符
    const identifierEl = page.querySelector('.identifier');
    if (identifierEl) identifierEl.textContent = this.identifier;

    // 页码
    const pageNumEl = page.querySelector('.page-number');
    if (pageNumEl) pageNumEl.textContent = String(pageNumber).padStart(2, '0');

    // 3 个 box
    const boxes = page.querySelectorAll('.box');
    boxes.forEach((box, i) => {
      box.innerHTML = ''; // 清模板内容
      box.innerHTML = '';
      //box.id = `box${i + 1}-p${String(pageNumber).padStart(2, '0')}`; // 唯一 id
      const row = pageData[i];
      if (row) box.appendChild(this.createBoxContent(row));
    });

    return page;
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
    console.log('createBoxContent 调用,rowData:', rowData);

    const content = document.createElement('div');
    content.className = 'event-content';

    const coordinate = rowData['B'] || '';      // 坐标
    const area = rowData['C'] || '';            // 区域
    const description = rowData['D'] || '';     // 事件内容
    const eventType = rowData['E'] || '';       // 事件类别
    const reward = rowData['F'] || '';          // 物资
    const isCompleted = rowData['I'] === '是' || rowData['I'] === 'true' || rowData['I'] === '完成' || rowData['I'] === '1';

    // 判断是否是后续剧情:物资为"-"表示这是后续剧情
    const isFollowUpEvent = reward === '-';

    console.log('提取的数据:', {
      coordinate, area, description, eventType, reward, isCompleted, isFollowUpEvent
    });

    // 图标类型映射表(6种图标类型)
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

    // 图标:使用CSS样式类
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

    // 如果是后续剧情,在图标后面添加 NEW! 标识
    if (isFollowUpEvent) {
      const newBadge = document.createElement('div');
      newBadge.className = 'event-new-badge';
      newBadge.textContent = 'NEW!';
      content.appendChild(newBadge);
    }

    // 地理位置:使用CSS样式类
    if (coordinate || area) {
      const location = document.createElement('div');
      location.className = 'event-location';
      location.textContent = `${coordinate}${area ? ' - ' + area : ''}`;
      content.appendChild(location);
    }

    // 事件描述:使用CSS样式类
    if (description) {
      const desc = document.createElement('div');
      desc.className = 'event-description';
      desc.textContent = description;
      content.appendChild(desc);
    }

    // 奖励:只有在不是后续剧情时才显示
    if (!isFollowUpEvent) {
      const rewardDiv = document.createElement('div');
      rewardDiv.className = 'event-reward';
      rewardDiv.textContent = isCompleted ? `获得物资:${reward}` : '获得物资:?';
      content.appendChild(rewardDiv);
    }

    // 如果已完成,添加遮罩
    if (isCompleted) {
      const mask = document.createElement('div');
      mask.className = 'event-mask';
      content.appendChild(mask);

      // 判定等级(S/A/B/C)
      const grade = (rowData['L'] || '').toUpperCase();
      const validGrades = ['S', 'A', 'B', 'C'];
      if (validGrades.includes(grade)) {
        const stamp = document.createElement('img');
        stamp.src = `./assets/img/stamp-${grade}.png`;
        stamp.className = 'event-stamp';
        content.appendChild(stamp);
      }
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

        // 找到统一缩放的容器
        const wrapper = page.closest('.page-wrapper') || document.getElementById('viewer');

        // 读取原始 scale（优先 inline，其次 computed）
        const inlineScale = wrapper?.style.getPropertyValue('--scale');
        const computedScale = wrapper ? getComputedStyle(wrapper).getPropertyValue('--scale') : '1';
        const originalScale = (inlineScale || computedScale || '1').trim();

        try {
          // 临时禁用统一缩放
          if (wrapper) wrapper.style.setProperty('--scale', '1');

          const canvas = await html2canvas(page, {
            width: 1230,
            height: 1729,
            scale: 2,            // 导出清晰度
            useCORS: true,
            backgroundColor: '#ffffff'
          });

          const link = document.createElement('a');
          link.download = `${this.identifier}-${String(pageNum).padStart(2, '0')}.png`;
          link.href = canvas.toDataURL('image/png');
          link.click();
        } finally {
          // 恢复统一缩放
          if (wrapper) wrapper.style.setProperty('--scale', originalScale || '1');
        }

        // 稍作间隔，避免阻塞 UI
        await new Promise(r => setTimeout(r, 200));
      }

      statusDiv.textContent = '导出完成！';
      setTimeout(() => (statusDiv.style.display = 'none'), 3000);
    } catch (error) {
      statusDiv.textContent = '导出失败: ' + error.message;
      console.error('Export error:', error);
    }


  }
}

// Initialize
window.addEventListener('load', () => {
  setupUnifiedZoomControl();
  applyAutoScale();

  setupControls();
  new LayoutGenerator();
});

window.addEventListener('resize', applyAutoScale);