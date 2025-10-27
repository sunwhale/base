// 简化的卡片状态管理器
const CardStateManager = {
  // 获取当前页面的标识符（基于URL）
  getPageIdentifier: function () {
    return window.currentPage || window.location.pathname || '/default';
  },

  // 获取存储键名
  getStorageKey: function () {
    return `card_states_${this.getPageIdentifier()}`;
  },

  // 保存卡片状态
  saveCardStates: function () {
    const cardStates = {};

    $('.card').each(function () {
      const cardId = $(this).data('card-id');
      const isCollapsed = $(this).find('.card-body').is(':hidden');

      if (cardId) {
        cardStates[cardId] = isCollapsed ? 'collapsed' : 'expanded';
      }
    });

    localStorage.setItem(this.getStorageKey(), JSON.stringify(cardStates));
    this.updateCardStatesInfo();
  },

  // 加载卡片状态
  loadCardStates: function () {
    const storedStates = localStorage.getItem(this.getStorageKey());

    if (storedStates) {
      try {
        const cardStates = JSON.parse(storedStates);

        $('.card').each(function () {
          const cardId = $(this).data('card-id');

          if (cardId && cardStates[cardId]) {
            const $cardBody = $(this).find('.card-body');
            const $cardHeader = $(this).find('.card-header');

            if (cardStates[cardId] === 'collapsed') {
              $cardBody.hide();
              $cardHeader.addClass('collapsed');
            } else {
              $cardBody.show();
              $cardHeader.removeClass('collapsed');
            }
          }
        });

        this.updateCardStatesInfo();
      } catch (e) {
        console.error('解析卡片状态失败:', e);
      }
    }
  },

  // 重置当前页面的卡片状态
  resetCurrentPageStates: function () {
    localStorage.removeItem(this.getStorageKey());

    $('.card').each(function () {
      const $cardBody = $(this).find('.card-body');
      const $cardHeader = $(this).find('.card-header');

      $cardBody.show();
      $cardHeader.removeClass('collapsed');
    });

    this.updateCardStatesInfo();
  },

  // 重置所有页面的卡片状态
  resetAllStates: function () {
    // 获取所有以"card_states_"开头的键
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('card_states_')) {
        localStorage.removeItem(key);
      }
    });

    $('.card').each(function () {
      const $cardBody = $(this).find('.card-body');
      const $cardHeader = $(this).find('.card-header');

      $cardBody.show();
      $cardHeader.removeClass('collapsed');
    });

    this.updateCardStatesInfo();
  },

  // 更新页面信息显示
  updatePageInfo: function () {
    $('#currentUrl').text(this.getPageIdentifier());
    $('#pageIdentifier').text(this.getStorageKey());
    this.updateCardStatesInfo();
  },

  // 更新卡片状态信息显示
  updateCardStatesInfo: function () {
    const cardStates = {};

    $('.card').each(function () {
      const cardId = $(this).data('card-id');
      const isCollapsed = $(this).find('.card-body').is(':hidden');

      if (cardId) {
        cardStates[cardId] = isCollapsed ? '折叠' : '展开';
      }
    });

    $('#cardStatesInfo').text(JSON.stringify(cardStates, null, 2));
  },

  // 初始化卡片状态管理器
  init: function () {
    // 初始化页面信息
    this.updatePageInfo();

    // 加载卡片状态
    this.loadCardStates();

    // 为卡片头部添加点击事件
    $('.card-header').on('click', function () {
      const $cardBody = $(this).closest('.card').find('.card-body');
      const $cardHeader = $(this);

      $cardBody.slideToggle(300, function () {
        $cardHeader.toggleClass('collapsed', !$cardBody.is(':visible'));
        CardStateManager.saveCardStates();
      });
    });

    console.log('卡片状态管理器已初始化');
  }
};

$(document).ready(function () {
  // 侧边栏状态存储键名
  const SIDEBAR_STATE_KEY = 'adminlte_sidebar_state';
  const SCROLL_POSITION_KEY = 'adminlte_scroll_position';

  // 检查并应用存储的侧边栏状态
  function applyStoredSidebarState() {
    const storedState = localStorage.getItem(SIDEBAR_STATE_KEY);

    if (storedState === 'collapsed') {
      // 如果存储的状态是折叠，则折叠侧边栏
      $('body').addClass('sidebar-collapse');
    } else {
      // 否则展开侧边栏
      $('body').removeClass('sidebar-collapse');
    }

    // 触发resize事件，确保布局正确
    $(window).trigger('resize');
  }

  // 监听侧边栏折叠/展开事件
  $('[data-widget="pushmenu"]').on('click', function () {
    // 延迟执行以确保类名已更新
    setTimeout(function () {
      const isCollapsed = $('body').hasClass('sidebar-collapse');

      // 存储当前状态
      if (isCollapsed) {
        localStorage.setItem(SIDEBAR_STATE_KEY, 'collapsed');
      } else {
        localStorage.setItem(SIDEBAR_STATE_KEY, 'expanded');
      }
    }, 100);
  });
  // 页面加载时应用存储的状态

  // 恢复滚动位置
  function restoreScrollPosition() {
    const savedPosition = localStorage.getItem(SCROLL_POSITION_KEY);
    if (savedPosition) {
      // 使用setTimeout确保DOM完全加载
      setTimeout(function () {
        $(window).scrollTop(savedPosition);
        updateScrollProgress();
      }, 100);
    }
  }

  // 更新滚动进度条
  function updateScrollProgress() {
    const windowHeight = $(window).height();
    const documentHeight = $(document).height();
    const scrollTop = $(window).scrollTop();
    const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;

    $('#scrollProgress').css('width', scrollPercent + '%');
  }

  // 监听滚动事件
  $(window).on('scroll', function () {
    // 使用防抖技术减少存储频率
    clearTimeout($.data(this, 'scrollTimer'));
    $.data(this, 'scrollTimer', setTimeout(function () {
      const scrollPosition = $(window).scrollTop();
      localStorage.setItem(SCROLL_POSITION_KEY, scrollPosition);

      updateScrollProgress();
    }, 250));
  });

  // 页面加载时应用存储的状态
  applyStoredSidebarState();
  restoreScrollPosition();
  window.currentPage = window.location.pathname;
  CardStateManager.init();

  // 初始化滚动进度条
  updateScrollProgress();
});