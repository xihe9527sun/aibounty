// AIbounty Analytics & SEO Scripts
// 百度自动推送 + JSON-LD 结构化数据
// 所有页面共享，方便维护

(function() {
  // 1. 百度自动推送 — 零成本让百度即时收录
  var bp = document.createElement('script');
  bp.src = 'https://zz.bdstatic.com/linksubmit/push.js';
  bp.async = true;
  var s = document.getElementsByTagName('script')[0];
  s.parentNode.insertBefore(bp, s);

  // 2. JSON-LD — 网站结构化数据（仅首页设置）
  // 如果页面还没有 JSON-LD，则添加
  if (!document.querySelector('script[type="application/ld+json"]')) {
    var ld = document.createElement('script');
    ld.type = 'application/ld+json';
    ld.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "AIbounty · AI 赏金猎人",
      "url": "https://www.aibounty.cn",
      "description": "每日精选全球 AI 社区好工具"
    });
    document.head.appendChild(ld);
  }
})();
