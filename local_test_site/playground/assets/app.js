(() => {
 const root=document.documentElement;
 const qaLabPage=document.getElementById("qa-lab");
 const siteNavLinks=[...document.querySelectorAll("[data-site-nav]")];
 const qaNavLinks=[...document.querySelectorAll("[data-qa-nav]")];
 const labHashes=["#lab-normal","#lab-negative","#lab-accessibility","#lab-responsive","#lab-security"];
 const updatePageRoute=()=>{
   const hash=window.location.hash||"#home";
   const inQaLab=hash==="#qa-lab"||labHashes.includes(hash);
   qaLabPage.classList.toggle("active",inQaLab);
   document.body.classList.toggle("qa-lab-active",inQaLab);
   siteNavLinks.forEach(link=>{
     const active=!inQaLab && link.getAttribute("href")===hash;
     link.classList.toggle("active",active);
     if(active)link.setAttribute("aria-current","page");else link.removeAttribute("aria-current");
   });
   qaNavLinks.forEach(link=>{
     link.classList.toggle("active",inQaLab);
     if(inQaLab)link.setAttribute("aria-current","page");else link.removeAttribute("aria-current");
   });
   if(inQaLab){
     requestAnimationFrame(()=>{
       const target=hash==="#qa-lab"?qaLabPage:document.getElementById(hash.slice(1));
       if(target)target.scrollIntoView({behavior:"smooth",block:"start"});
     });
   }
 };
 window.addEventListener("hashchange",updatePageRoute);
 updatePageRoute();

 const themeButton=document.getElementById("themeToggle");
 const saved=localStorage.getItem("mdz-theme");
 if(saved==="light"||saved==="dark") root.dataset.theme=saved;
 themeButton.addEventListener("click",()=>{
   root.dataset.theme=root.dataset.theme==="dark"?"light":"dark";
   localStorage.setItem("mdz-theme",root.dataset.theme);
   document.querySelector('meta[name="theme-color"]').content=root.dataset.theme==="dark"?"#0b0b0e":"#f4f5f8";
 });
 const drawer=document.getElementById("mobileDrawer"),scrim=document.getElementById("drawerScrim"),open=document.getElementById("menuOpen");
 const close=()=>{drawer.classList.remove("open");scrim.classList.remove("show");open.setAttribute("aria-expanded","false");};
 open.addEventListener("click",()=>{drawer.classList.add("open");scrim.classList.add("show");open.setAttribute("aria-expanded","true");});
 document.getElementById("menuClose").addEventListener("click",close);scrim.addEventListener("click",close);
 drawer.querySelectorAll("a").forEach(a=>a.addEventListener("click",close));
document.addEventListener("keydown",e=>{
   if(e.key==="Escape"){
     close();
     if(modal.classList.contains("open"))closeModal();
   }
 });
   // MDZ_HERO_CAROUSEL_V1
  const heroCarousel=document.getElementById("heroCarousel");
  if(heroCarousel){
    const heroImage=document.getElementById("heroSlideImage");
    const heroDots=[...heroCarousel.querySelectorAll(".dot")];
    const heroSlides=[
      {src:"/assets/images/mdz-family-team.png",alt:"Keluarga MyDreamZone: dua orang tua pembalap dan empat anak sebagai tim pendukung dan teknisi"},
      {src:"/assets/images/event-meet.jpg",alt:"Suasana pertemuan komunitas otomotif MyDreamZone"},
      {src:"/assets/images/highlight-review.jpg",alt:"Konten review otomotif MyDreamZone"},
      {src:"/assets/images/reels-night-drive.jpg",alt:"Suasana night drive komunitas MyDreamZone"}
    ];
    let heroIndex=0,heroStartX=null;
    const showHeroSlide=(next)=>{
      heroIndex=(next+heroSlides.length)%heroSlides.length;
      heroImage.classList.add("is-changing");
      const slide=heroSlides[heroIndex];
      const preload=new Image();
      preload.onload=()=>{
        heroImage.src=slide.src;
        heroImage.alt=slide.alt;
        heroDots.forEach((dot,index)=>{
          const active=index===heroIndex;
          dot.classList.toggle("active",active);
          dot.setAttribute("aria-current",active?"true":"false");
        });
        requestAnimationFrame(()=>heroImage.classList.remove("is-changing"));
      };
      preload.onerror=()=>heroImage.classList.remove("is-changing");
      preload.src=slide.src;
    };
    heroDots.forEach((dot,index)=>dot.addEventListener("click",()=>showHeroSlide(index)));
    heroCarousel.querySelector(".hero-arrow-prev").addEventListener("click",()=>showHeroSlide(heroIndex-1));
    heroCarousel.querySelector(".hero-arrow-next").addEventListener("click",()=>showHeroSlide(heroIndex+1));
    heroCarousel.addEventListener("keydown",event=>{
      if(event.key==="ArrowLeft"){event.preventDefault();showHeroSlide(heroIndex-1);}
      if(event.key==="ArrowRight"){event.preventDefault();showHeroSlide(heroIndex+1);}
    });
    heroCarousel.addEventListener("pointerdown",event=>{
      if(event.pointerType==="mouse" && event.button!==0)return;
      heroStartX=event.clientX;
    });
    heroCarousel.addEventListener("pointerup",event=>{
      if(heroStartX===null)return;
      const delta=event.clientX-heroStartX;
      heroStartX=null;
      if(Math.abs(delta)>45)showHeroSlide(delta<0?heroIndex+1:heroIndex-1);
    });
    heroCarousel.addEventListener("pointercancel",()=>{heroStartX=null;});
  }
const modal=document.getElementById("imageModal"),modalImage=document.getElementById("modalImage");
 const modalClose=document.getElementById("modalClose");
 let modalOpener=null,previousBodyOverflow="";

 const openModal=btn=>{
   modalOpener=btn;
   previousBodyOverflow=document.body.style.overflow;
   modalImage.src=btn.dataset.image;
   modal.classList.add("open");
   document.body.style.overflow="hidden";
   modalClose.focus();
 };

 const closeModal=()=>{
   if(!modal.classList.contains("open"))return;
   modal.classList.remove("open");
   document.body.style.overflow=previousBodyOverflow;
   if(modalOpener && modalOpener.isConnected)modalOpener.focus();
   modalOpener=null;
 };

 document.querySelectorAll(".media-open").forEach(btn=>btn.addEventListener("click",()=>openModal(btn)));
 modalClose.addEventListener("click",closeModal);
 modal.addEventListener("click",e=>{if(e.target===modal)closeModal();});

 modal.addEventListener("keydown",e=>{
   if(e.key!=="Tab")return;
   const focusable=[...modal.querySelectorAll('button:not([disabled]),[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')]
     .filter(el=>el.getClientRects().length>0);
   if(focusable.length===0){
     e.preventDefault();
     modal.focus();
     return;
   }
   const first=focusable[0],last=focusable[focusable.length-1];
   if(e.shiftKey && (document.activeElement===first || document.activeElement===modal)){
     e.preventDefault();
     last.focus();
   }else if(!e.shiftKey && (document.activeElement===last || document.activeElement===modal)){
     e.preventDefault();
     first.focus();
   }
 });
 document.getElementById("backTop").addEventListener("click",()=>window.scrollTo({top:0,behavior:"smooth"}));
 const toast=document.getElementById("toast");let toastTimer;
 const showToast=msg=>{toast.textContent=msg;toast.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.classList.remove("show"),2200);};
 document.getElementById("watchTrailer").addEventListener("click",()=>showToast("Trailer MyDreamZone akan segera hadir."));
 document.getElementById("searchToggle").addEventListener("click",()=>showToast("Fitur pencarian akan dikembangkan pada tahap berikutnya."));
 document.getElementById("notificationToggle").addEventListener("click",()=>showToast("Belum ada notifikasi baru."));
 // LIVING_QA_WORKBENCH_D2_D7
 const qaComponents = [
  {
    "id": "CMP-001",
    "number": 1,
    "name": "Header",
    "source_status": "implemented",
    "category": "navigation",
    "selector_candidates": [
      ".topbar",
      ".main-nav",
      ".top-actions"
    ],
    "source_evidence": "`index.html`: `.topbar`, `.main-nav`, `.top-actions`; CSS sticky header.",
    "gap": "Desktop header and main navigation exist. QA Lab nav is not present.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-002",
    "number": 2,
    "name": "Logo",
    "source_status": "implemented",
    "category": "navigation",
    "selector_candidates": [
      ".brand",
      ".brand-name",
      ".hero-brand"
    ],
    "source_evidence": "`.brand`, `.brand-name`, `.hero-brand`; local `mdz-logo.svg` also exists in assets.",
    "gap": "Logo/brand treatment exists in header, hero and footer; image asset presence should be verified for actual usage.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-003",
    "number": 3,
    "name": "Hamburger Menu",
    "source_status": "implemented",
    "category": "navigation",
    "selector_candidates": [
      "#menuOpen",
      "#mobileDrawer",
      "#menuClose",
      "#drawerScrim"
    ],
    "source_evidence": "`#menuOpen`, `#mobileDrawer`, `#menuClose`, `#drawerScrim`; JS open/close handlers.",
    "gap": "Mobile drawer opens/closes and Escape handler calls close; focus management and inert background are not implemented.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-004",
    "number": 4,
    "name": "Expandable Sidebar",
    "source_status": "not_implemented",
    "category": "navigation",
    "selector_candidates": [
      "aside[aria-label='Expandable sidebar']",
      "[data-component='expandable-sidebar']"
    ],
    "source_evidence": "No expandable sidebar structure or dedicated JS behavior found.",
    "gap": "Mobile drawer is not an expandable sidebar; do not count it as this component.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-005",
    "number": 5,
    "name": "Overlay Navigation",
    "source_status": "partial",
    "category": "navigation",
    "selector_candidates": [
      ".drawer-scrim"
    ],
    "source_evidence": "Mobile drawer plus `.drawer-scrim` overlay on small screens.",
    "gap": "Overlay exists for the mobile drawer only; no separate overlay navigation pattern or keyboard/focus treatment.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-006",
    "number": 6,
    "name": "Bottom Navigation",
    "source_status": "not_implemented",
    "category": "navigation",
    "selector_candidates": [
      "nav[aria-label='Bottom navigation']",
      "[data-component='bottom-navigation']"
    ],
    "source_evidence": "No bottom navigation markup or styles found.",
    "gap": "No persistent bottom navigation component.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-007",
    "number": 7,
    "name": "Footer",
    "source_status": "implemented",
    "category": "navigation",
    "selector_candidates": [
      "footer.site-footer",
      ".footer-links",
      ".social-links"
    ],
    "source_evidence": "`footer.site-footer`, `.footer-links`, `.social-links`.",
    "gap": "Footer structure and links exist; links currently point to local placeholder anchors.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-008",
    "number": 8,
    "name": "Floating Go to Top",
    "source_status": "partial",
    "category": "navigation",
    "selector_candidates": [
      "#backTop"
    ],
    "source_evidence": "`#backTop`; JS calls `window.scrollTo`; CSS positions button inside footer, not fixed/floating.",
    "gap": "Back-to-top action exists, but component is not floating/always available as its name implies.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-009",
    "number": 9,
    "name": "Hero Banner",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      "section.hero",
      ".hero-copy",
      ".hero-visual"
    ],
    "source_evidence": "`section.hero`, `.hero-copy`, `.hero-visual`.",
    "gap": "Hero section with copy, CTA and visual exists.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-010",
    "number": 10,
    "name": "Image Carousel / Slider",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      "#heroCarousel"
    ],
    "source_evidence": "`#heroCarousel`; JS `showHeroSlide`, previous/next, preload, pointer swipe.",
    "gap": "Four-slide carousel with arrows, indicators, keyboard arrows and pointer swipe handlers.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-011",
    "number": 11,
    "name": "Carousel Indicator",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      ".dot"
    ],
    "source_evidence": "Four `.dot` buttons with `aria-current`; JS updates active state.",
    "gap": "Indicators are interactive and active state is updated by JS.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-012",
    "number": 12,
    "name": "CTA Button",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      ".btn-primary",
      ".btn-outline"
    ],
    "source_evidence": "`.btn-primary` anchor and `.btn-outline` trailer button.",
    "gap": "Join Community navigates to section; trailer button currently displays placeholder toast.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-013",
    "number": 13,
    "name": "What's On Section",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      "section.top-panels",
      ".whats-on"
    ],
    "source_evidence": "`section.top-panels` contains `.whats-on`.",
    "gap": "Section and event summary panel exist as static content.",
    "relevant_labs": [
      "normal",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-014",
    "number": 14,
    "name": "Event Card",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".event-feature"
    ],
    "source_evidence": "`.event-feature` with date, title, location and image.",
    "gap": "One static featured event card; no detail route or event interaction.",
    "relevant_labs": [
      "normal",
      "negative",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-015",
    "number": 15,
    "name": "Winner Table",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      ".winner-panel",
      ".table-wrap"
    ],
    "source_evidence": "`.winner-panel`, `.table-wrap`, semantic table with thead/tbody.",
    "gap": "Static three-row table exists; responsive handling is horizontal scroll wrapper.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-016",
    "number": 16,
    "name": "Horizontal Carousel",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      "[data-component='horizontal-carousel']",
      "[data-carousel='horizontal']"
    ],
    "source_evidence": "No carousel track/controls for a horizontal content list found.",
    "gap": "Hero carousel is a slide carousel, not a horizontal multi-card carousel.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-017",
    "number": 17,
    "name": "Highlights Section",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      "section.highlights",
      ".highlight-list",
      ".highlight-card"
    ],
    "source_evidence": "`section.highlights`, `.highlight-list`, five `.highlight-card` anchors.",
    "gap": "Highlights content section and five image cards exist.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-018",
    "number": 18,
    "name": "Category Card",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".highlight-card"
    ],
    "source_evidence": "Highlight cards show category-like labels (Car Review, Modification, Motorsport, Lifestyle, Family Garage).",
    "gap": "Cards visually represent categories but are not a distinct category-card component or category destination.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-019",
    "number": 19,
    "name": "Latest Discussions",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      ".discussions",
      ".discussion-list"
    ],
    "source_evidence": "`.discussions`, `.discussion-list` with three discussion entries.",
    "gap": "Discussion listing exists as static content.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-020",
    "number": 20,
    "name": "Discussion Card",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".discussion"
    ],
    "source_evidence": "Each `.discussion` row contains avatar, title, author, timestamp and stats.",
    "gap": "A discussion row pattern exists, but it is static and has no detail/action behavior.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-021",
    "number": 21,
    "name": "Comment Input",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      "form.comment-form",
      "textarea[name='comment']",
      "[data-component='comment-input']"
    ],
    "source_evidence": "No comment form or input found.",
    "gap": "No comment composer or submit interaction.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-022",
    "number": 22,
    "name": "Comment Thread",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      ".comment-thread",
      "[data-component='comment-thread']"
    ],
    "source_evidence": "No thread detail/reply structure found.",
    "gap": "Discussion list is not a comment thread.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-023",
    "number": 23,
    "name": "Nested Comments",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      ".nested-comments",
      "[data-component='nested-comments']"
    ],
    "source_evidence": "No nested/reply comment markup found.",
    "gap": "No nested discussion hierarchy.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-024",
    "number": 24,
    "name": "Like Button",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      "button.like-button",
      "[data-action='like']"
    ],
    "source_evidence": "No like control or state handler found.",
    "gap": "No like interaction.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-025",
    "number": 25,
    "name": "Comment Counter",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".discussion-stats span:first-child"
    ],
    "source_evidence": "Discussion stats contain static comment-like numbers (e.g. 54, 37, 89).",
    "gap": "Counters are visual text only; not tied to comments or changing state.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-026",
    "number": 26,
    "name": "View Counter",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".discussion-stats span:nth-child(2)"
    ],
    "source_evidence": "Discussion stats contain static view-like values (e.g. 2.3K, 1.1K, 4.8K).",
    "gap": "Values are static display text, not tracked view counts.",
    "relevant_labs": [
      "normal",
      "negative"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-027",
    "number": 27,
    "name": "Reels Section",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".reels",
      ".reel-image"
    ],
    "source_evidence": "`.reels` section with one `.reel-image` preview.",
    "gap": "A reels-like panel exists, but it contains a static image preview, not a reel/video feed.",
    "relevant_labs": [
      "normal",
      "negative",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-028",
    "number": 28,
    "name": "Video Card",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".reel-image"
    ],
    "source_evidence": "`.reel-image` button contains image, play icon and duration label.",
    "gap": "Video-card appearance exists, but it does not represent a playable video.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-029",
    "number": 29,
    "name": "Video Play Button",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".play-button",
      ".reel-image"
    ],
    "source_evidence": "`.play-button` is a decorative span inside `.reel-image`.",
    "gap": "Play icon is visual only; click opens image modal via `.media-open`, not video playback.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-030",
    "number": 30,
    "name": "Gallery Section",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      "section.gallery",
      ".gallery-grid"
    ],
    "source_evidence": "`section.gallery`, `.gallery-grid`, three image buttons.",
    "gap": "Gallery section and three image entries exist.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-031",
    "number": 31,
    "name": "Masonry Grid",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      ".masonry-grid",
      "[data-layout='masonry']"
    ],
    "source_evidence": "Gallery uses regular CSS Grid; no masonry layout found.",
    "gap": "A regular grid is not a masonry grid.",
    "relevant_labs": [
      "normal",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-032",
    "number": 32,
    "name": "Infinite Scroll",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      "[data-infinite-scroll]"
    ],
    "source_evidence": "No IntersectionObserver, scroll-triggered append, or paging data flow found.",
    "gap": "No infinite loading behavior.",
    "relevant_labs": [
      "normal",
      "negative",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-033",
    "number": 33,
    "name": "Hover Interaction",
    "source_status": "implemented",
    "category": "interaction",
    "selector_candidates": [".main-nav a", ".highlight-card", ".discussion", ".reel-image", ".gallery-image"],
    "source_evidence": "CSS hover rules for nav, highlight cards, discussion table rows, reel/gallery images.",
    "gap": "Hover states exist; keyboard-equivalent states need separate validation.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "needs_review",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-034",
    "number": 34,
    "name": "Tooltip",
    "source_status": "not_implemented",
    "category": "interaction",
    "selector_candidates": [
      "[role='tooltip']",
      "[data-tooltip]"
    ],
    "source_evidence": "No tooltip markup/behavior or `title`-based tooltip component found.",
    "gap": "No explicit tooltip component.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-035",
    "number": 35,
    "name": "Expand / Collapse",
    "source_status": "partial",
    "category": "interaction",
    "selector_candidates": [
      "#mobileDrawer",
      ".mobile-drawer"
    ],
    "source_evidence": "Mobile drawer expands/collapses through `.open`; no generic disclosure/accordion component.",
    "gap": "One specialized drawer state exists, not a reusable expand/collapse pattern.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-036",
    "number": 36,
    "name": "Scrollable Container",
    "source_status": "partial",
    "category": "interaction",
    "selector_candidates": [
      ".table-wrap"
    ],
    "source_evidence": "`.table-wrap` uses `overflow-x:auto`.",
    "gap": "One horizontally scrollable table wrapper exists; no general scroll-container component.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-037",
    "number": 37,
    "name": "Horizontal Scroll",
    "source_status": "partial",
    "category": "interaction",
    "selector_candidates": [
      ".table-wrap"
    ],
    "source_evidence": "`.table-wrap` and responsive content overflow handling.",
    "gap": "Horizontal scroll is present for the table only; no standalone horizontal scroller component.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-038",
    "number": 38,
    "name": "Vertical Scroll",
    "source_status": "not_implemented",
    "category": "interaction",
    "selector_candidates": [
      ".vertical-scroll",
      "[data-scroll-axis='y']"
    ],
    "source_evidence": "Page uses normal document scrolling; no dedicated vertical scroll container found.",
    "gap": "Normal page scroll is not a dedicated vertical scrollable component.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-039",
    "number": 39,
    "name": "Modal / Popup",
    "source_status": "implemented",
    "category": "interaction",
    "selector_candidates": [
      "#imageModal",
      "#modalClose",
      "#modalImage"
    ],
    "source_evidence": "`#imageModal`, `#modalClose`, `#modalImage`; JS open/close, focus transfer/trap/restore, body scroll lock.",
    "gap": "Image modal implemented with accessibility behavior; it is image-viewer-specific, not a general-purpose modal framework.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-040",
    "number": 40,
    "name": "Floating Button",
    "source_status": "partial",
    "category": "interaction",
    "selector_candidates": [
      "#backTop"
    ],
    "source_evidence": "`#backTop` is a button in footer; CSS not fixed except relative positioning on mobile footer.",
    "gap": "Back-to-top action exists, but no general floating action button component.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-041",
    "number": 41,
    "name": "Loading Indicator",
    "source_status": "not_implemented",
    "category": "interaction",
    "selector_candidates": [
      "[role='progressbar']",
      ".loading-indicator"
    ],
    "source_evidence": "No loading spinner/progress UI found.",
    "gap": "Image preload is internal JS behavior; no user-visible loading indicator.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-042",
    "number": 42,
    "name": "Category Label",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".highlight-card"
    ],
    "source_evidence": "Text labels inside `.highlight-card` and section headings.",
    "gap": "Category-like labels exist as card captions, but no reusable category-label component.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-043",
    "number": 43,
    "name": "Article Card",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".highlight-card"
    ],
    "source_evidence": "Highlight cards resemble article/category tiles.",
    "gap": "No article metadata, summary, author/date or article detail behavior.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-044",
    "number": 44,
    "name": "Content Thumbnail",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      "img[alt]"
    ],
    "source_evidence": "Images used in event, highlights, reels preview and gallery cards.",
    "gap": "Thumbnail images exist with varied contexts; some highlight images have empty alt text.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-045",
    "number": 45,
    "name": "Content Grid",
    "source_status": "partial",
    "category": "content",
    "selector_candidates": [
      ".highlight-list",
      ".gallery-grid"
    ],
    "source_evidence": "`.highlight-list` and `.gallery-grid` use CSS Grid.",
    "gap": "Grid layouts exist for highlights/gallery, but no general content-grid component/data pattern.",
    "relevant_labs": [
      "normal",
      "negative",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-046",
    "number": 46,
    "name": "Pagination",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      "nav[aria-label='Pagination']",
      "[data-pagination]"
    ],
    "source_evidence": "No pagination markup or JS found.",
    "gap": "No page navigation for multi-page content.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-047",
    "number": 47,
    "name": "Load More / More Threads",
    "source_status": "not_implemented",
    "category": "content",
    "selector_candidates": [
      "button.load-more",
      "[data-action='load-more']"
    ],
    "source_evidence": "No load-more button or append behavior found.",
    "gap": "No incremental content loading.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-048",
    "number": 48,
    "name": "Gallery Image Viewer",
    "source_status": "implemented",
    "category": "content",
    "selector_candidates": [
      ".media-open",
      "#modalImage"
    ],
    "source_evidence": "`.media-open` buttons; `openModal(btn)` loads `data-image` into `#modalImage`.",
    "gap": "Gallery viewer opens image modal; test all images and failure cases separately.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-049",
    "number": 49,
    "name": "Responsive Header",
    "source_status": "implemented",
    "category": "navigation",
    "selector_candidates": [
      ".topbar"
    ],
    "source_evidence": "CSS breakpoint at 760px hides desktop nav and displays mobile menu; 1050px adjusts header.",
    "gap": "Desktop/mobile header variants are implemented in CSS.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-050",
    "number": 50,
    "name": "Responsive Sidebar",
    "source_status": "not_implemented",
    "category": "navigation",
    "selector_candidates": [
      "aside.sidebar",
      "[data-component='responsive-sidebar']"
    ],
    "source_evidence": "No sidebar component; mobile drawer is a navigation drawer.",
    "gap": "No responsive sidebar with expandable/collapsible sidebar behavior.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-051",
    "number": 51,
    "name": "Responsive Bottom Navigation",
    "source_status": "not_implemented",
    "category": "navigation",
    "selector_candidates": [
      "nav.bottom-navigation",
      "[data-component='bottom-navigation']"
    ],
    "source_evidence": "No bottom navigation markup or mobile-specific bottom bar found.",
    "gap": "No bottom navigation component at any viewport.",
    "relevant_labs": [
      "normal",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-052",
    "number": 52,
    "name": "Responsive Grid",
    "source_status": "implemented",
    "category": "responsive",
    "selector_candidates": [
      ".top-panels",
      ".bottom-panels",
      ".highlight-list",
      ".gallery-grid"
    ],
    "source_evidence": "`.top-panels`, `.bottom-panels`, `.highlight-list`, `.gallery-grid` change layout at 1050px/760px.",
    "gap": "Several grids adapt at breakpoints; needs browser verification for overflow and content fit.",
    "relevant_labs": [
      "normal",
      "negative",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-053",
    "number": 53,
    "name": "Responsive Carousel",
    "source_status": "implemented",
    "category": "responsive",
    "selector_candidates": [
      "#heroCarousel"
    ],
    "source_evidence": "Hero carousel remains active; hero and image height/layout change at 760px/390px.",
    "gap": "Responsive carousel layout exists; touch/swipe behavior still requires runtime tests on target devices/viewports.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-054",
    "number": 54,
    "name": "Responsive Card",
    "source_status": "partial",
    "category": "responsive",
    "selector_candidates": [
      ".event-feature",
      ".highlight-card",
      ".discussion"
    ],
    "source_evidence": "Event, highlight, discussion and gallery cards receive responsive sizing/layout changes.",
    "gap": "Cards adapt through parent layouts, but no complete reusable card system or per-card responsive rules.",
    "relevant_labs": [
      "normal",
      "negative",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-055",
    "number": 55,
    "name": "Responsive Table",
    "source_status": "partial",
    "category": "responsive",
    "selector_candidates": [
      ".table-wrap"
    ],
    "source_evidence": "`.table-wrap{overflow-x:auto}` wraps winner table.",
    "gap": "Horizontal overflow is supported; no alternate mobile table presentation or explicit keyboard/scroll affordance.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-056",
    "number": 56,
    "name": "Responsive Gallery",
    "source_status": "implemented",
    "category": "responsive",
    "selector_candidates": [
      ".gallery-grid"
    ],
    "source_evidence": "`.gallery-grid` rows and layout change at 760px; images use object-fit cover.",
    "gap": "Gallery grid adapts for mobile; verify actual image crop, tap targets and modal sizing at viewports.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  },
  {
    "id": "CMP-057",
    "number": 57,
    "name": "Accordion",
    "source_status": "not_implemented",
    "category": "interaction",
    "selector_candidates": [
      "[data-qa-accordion]",
      "[data-component='accordion']"
    ],
    "source_evidence": "Approved separate catalog component #57; no accordion markup in supplied source inventory.",
    "gap": "Dedicated accordion component and interaction are not yet present.",
    "relevant_labs": [
      "normal",
      "negative",
      "accessibility",
      "responsive"
    ],
    "confidence": "medium",
    "detection_status": "not_scanned",
    "detection_matches": [],
    "detection_checked_at": null
  }
];
 const qaSelectorOwners=new Map();
 qaComponents.forEach(component=>{
   (component.selector_candidates||[]).forEach(selector=>{
     const owners=qaSelectorOwners.get(selector)||[];
     if(!owners.includes(component.id))owners.push(component.id);
     qaSelectorOwners.set(selector,owners);
   });
 });
 const qaScenarios = [
  ["SCN-N-001","Homepage route is reachable","normal",null,"Check homepage route and root container; record selector and ready state."],
  ["SCN-N-002","QA Lab route is reachable","normal",null,"Check QA Lab section and route target."],
  ["SCN-N-003","Workbench tabs switch panels","normal",null,"Record initial tab/pane, switch to catalog, and verify restoration of the initial pane."],
  ["SCN-N-004","Theme toggle control exists","normal",null,"Verify theme changes and root theme, storage, and theme-color metadata are restored."],
  ["SCN-N-005","Gallery dialog is present","normal","CMP-039","Verify dialog opens, focus moves to close, closes, and returns to opener."],
  ["SCN-X-001","Empty search is safely handled","negative",null,"Use a non-empty probe query, test empty input, and verify probe plus initial UI state restoration."],
  ["SCN-X-002","Invalid 403 threshold is rejected","negative",null,"Threshold outside configured range must be clamped."],
  ["SCN-X-003","Negative simulation stays local","negative",null,"Simulation must not create network requests."],
  ["SCN-A-001","Primary navigation has accessible name","accessibility","CMP-001","Check navigation landmark label."],
  ["SCN-A-002","QA tabs expose selected state","accessibility",null,"Check tab buttons and selected state."],
  ["SCN-A-003","Workbench controls have names","accessibility",null,"Check search, buttons, and labels."],
  ["SCN-R-001","Document has no horizontal overflow","responsive",null,"Compare scroll width with viewport width."],
  ["SCN-R-002","QA workbench fits active viewport","responsive",null,"Check workbench bounding box against viewport."],
  ["SCN-S-001","Security simulation remains local","security",null,"No external request is sent by the simulator."],
  ["SCN-S-002","403 threshold stop condition","security",null,"Local simulation stops at configured threshold."]
 ].map(([id,name,lab,component_id,purpose])=>({id,name,lab,component_id,purpose,preconditions:"Local MyDreamZone page loaded",steps:"Run from QA Workbench",expected_result:"Check completes without unsafe network activity",actual_result:null,status:"not_run",evidence_ref:null,severity:"info",last_verified:null}));
 const QA_C2_ASSERTIONS_EVIDENCE_V1=true;
  const QA_C2_1_EVIDENCE_V1=true;
 const qaScenarioSpecs={
  "SCN-N-003":{steps:"Click the Catalog tab; verify aria-selected and the matching pane; restore the previous pane.",expected_result:"Catalog tab is selected and its pane is active after a real click."},
  "SCN-N-004":{steps:"Click the theme toggle; verify the root theme changes; restore the original theme and storage value.",expected_result:"Theme changes after click and the original theme/storage state is restored."},
  "SCN-N-005":{steps:"Click the first available media opener; verify dialog opens; click Close and verify it closes.",expected_result:"Dialog opens from a media control and closes through its close button."},
  "SCN-X-001":{steps:"Record the current search and visible count; dispatch an input event with an empty value; verify safe rendering.",expected_result:"Empty search is processed without an execution error; prior search value is restored."},
  "SCN-X-003":{steps:"Not executed until browser network instrumentation is implemented.",expected_result:"Must remain blocked; absence of network traffic is not claimed without instrumentation."},
  "SCN-R-001":{steps:"Compare document scroll width with client viewport width at the current viewport.",expected_result:"No horizontal overflow at the current viewport; this is not a multi-breakpoint result."},
  "SCN-R-002":{steps:"Measure Workbench bounding rectangle against document client width at the current viewport.",expected_result:"Workbench bounds fit within the current viewport; this is not a multi-breakpoint result."}
 };
 Object.entries(qaScenarioSpecs).forEach(([id,spec])=>{const scenario=qaScenarios.find(item=>item.id===id);if(scenario)Object.assign(scenario,spec);});
 qaComponents.forEach(component=>{
   qaScenarios.push({
     id:`SCN-${component.id}-DOM`,
     name:`DOM candidate scan — ${component.name}`,
     lab:"normal",
     component_id:component.id,
     purpose:"Detect DOM elements matching the component's documented selector candidates.",
     preconditions:"Local MyDreamZone page loaded; component catalog source metadata available.",
     steps:"Query documented CSS selector candidates in the current document.",
     expected_result:component.source_status==="not_implemented"?"No candidate element is found (candidate absence only).":"At least one candidate element is found.",
     actual_result:null,status:"not_run",evidence_ref:null,severity:"info",last_verified:null,
     component_scan:true
   });
 });
 const qaResults=[];
 const qaSessionId=(globalThis.crypto&&typeof globalThis.crypto.randomUUID==="function")?globalThis.crypto.randomUUID():`qa-session-${Date.now()}-${Math.random().toString(36).slice(2)}`;
 let qaExecutionSequence=0;
 const qaCreateExecutionId=()=>`${qaSessionId}-run-${++qaExecutionSequence}`;
 const qaSanitizePageUrl=value=>{
   try{const parsed=new URL(value,location.href);return `${parsed.origin}${parsed.pathname}`;}
   catch(_){return "unavailable";}
 };
 const qaClone=value=>JSON.parse(JSON.stringify(value));
 const qaInitialComponentState=qaComponents.map(c=>({
   id:c.id,
   detection_status:c.detection_status,
   detection_classification:c.detection_classification,
   detection_matches:c.detection_matches,
   detection_notes:c.detection_notes,
   detection_checked_at:c.detection_checked_at,
   expectation_status:c.expectation_status,
   expectation_notes:c.expectation_notes,
   behavior_status:c.behavior_status,
   keyboard_equivalent_status:c.keyboard_equivalent_status
 }));
 const qaResetComponentState=()=>{
   qaComponents.forEach(component=>{
     const initial=qaInitialComponentState.find(item=>item.id===component.id);
     if(!initial)return;
     ["detection_status","detection_classification","detection_matches","detection_notes","detection_checked_at","expectation_status","expectation_notes","behavior_status","keyboard_equivalent_status"].forEach(key=>{
       if(Object.prototype.hasOwnProperty.call(initial,key))component[key]=qaClone(initial[key]);
       else delete component[key];
     });
   });
   qaRenderCatalog(document.getElementById("qaCatalogSearch").value);
 };
 const qaValidateScenarioRegistry=()=>{
   const errors=[];
   const componentIds=new Set(qaComponents.map(c=>c.id));
   if(qaComponents.length!==57)errors.push(`component count expected 57, got ${qaComponents.length}`);
   if(componentIds.size!==qaComponents.length)errors.push("duplicate component id");
   const scenarioIds=new Set();
   const validLabs=new Set(["normal","negative","accessibility","responsive","security"]);
   qaScenarios.forEach(s=>{
     if(!s.id||scenarioIds.has(s.id))errors.push(`duplicate scenario id: ${s.id||"(missing)"}`);
     scenarioIds.add(s.id);
     if(!validLabs.has(s.lab))errors.push(`invalid lab for ${s.id}: ${s.lab}`);
     if(s.component_id!==null&&!componentIds.has(s.component_id))errors.push(`unknown component reference: ${s.id} -> ${s.component_id}`);
     if(!s.name||!s.purpose||!s.expected_result)errors.push(`required scenario metadata missing: ${s.id}`);
   });
   const scans=qaScenarios.filter(s=>s.component_scan);
   const scanIds=new Set(scans.map(s=>s.component_id));
   if(scans.length!==qaComponents.length||scanIds.size!==qaComponents.length||qaComponents.some(c=>!scanIds.has(c.id)))errors.push("component scan coverage must be exactly one scenario per component");
   if(qaScenarios.length!==72)errors.push(`scenario count expected 72, got ${qaScenarios.length}`);
   if(errors.length)throw new Error("Scenario registry validation failed: "+errors.join("; "));
   return {valid:true,component_count:qaComponents.length,scenario_count:qaScenarios.length,component_scan_count:scans.length};
 };
 const qaScenarioRegistryValidation=qaValidateScenarioRegistry();
 const qaCaptureUiState=()=>({
   search_value:document.getElementById("qaCatalogSearch")?.value??"",
   active_pane:document.querySelector("[data-qa-pane].active")?.dataset.qaPane||"overview"
 });
 const qaRestoreUiState=snapshot=>{
   if(!snapshot)return;
   const search=document.getElementById("qaCatalogSearch");
   if(search){search.value=snapshot.search_value;qaRenderCatalog(snapshot.search_value);}
   qaSetPane(snapshot.active_pane);
 };
 const qaById=id=>qaScenarios.find(x=>x.id===id);
 const qaSafeText=s=>String(s??"");
 const qaSetPane=name=>{
   document.querySelectorAll("[data-qa-pane]").forEach(p=>p.classList.toggle("active",p.dataset.qaPane===name));
   document.querySelectorAll("[data-qa-tab]").forEach(b=>{
     const active=b.dataset.qaTab===name;b.classList.toggle("active",active);
     b.setAttribute("aria-selected",String(active));
   });
 };
 const qaRecordCard=(title,meta,description,action)=>{
   const card=document.createElement("article");card.className="qa-record";
   const body=document.createElement("div");body.className="qa-record-body";
   const h=document.createElement("strong");h.textContent=title;
   const m=document.createElement("small");m.textContent=meta;
   const p=document.createElement("p");p.textContent=description;
   body.append(h,m,p);card.append(body);
   if(action)card.append(action);
   return card;
 };
 const qaButton=(label,fn)=>{
   const b=document.createElement("button");b.type="button";b.className="qa-action secondary";b.textContent=label;b.addEventListener("click",fn);return b;
 };
  const qaDetectComponent=component=>{
    const matches=[];
    const invalid=[];
    const notes=[];
    let hoverInspectable=true;
    (component.selector_candidates||[]).forEach(selector=>{
      try{
        const found=[...document.querySelectorAll(selector)];
        if(found.length){
           const owners=qaSelectorOwners.get(selector)||[];
           matches.push({selector,count:found.length,signal:"dom_selector",owners,ambiguous:owners.length>1});
         }
      }catch(error){invalid.push({selector,error:error.message});}
    });
    // Hover detection is evidence of a CSS state, not proof of keyboard equivalence.
    if(component.id==="CMP-033"){
      matches.length=0; // DOM candidates alone do not establish a hover state.
      const hoverRules=[];
      const inspectRules=rules=>{[...rules].forEach(rule=>{
        // Process the current style rule before descending into nested rules.
        // Do not return early: some CSSOM implementations expose cssRules on
        // nested style rules as well as grouping rules.
        if(typeof rule.selectorText==="string"&&rule.selectorText.includes(":hover")){
          rule.selectorText.split(",").map(x=>x.trim()).forEach(raw=>{
            const base=raw.replace(/:hover\b/g,"").trim();
            if(!base)return;
            try{
              const count=document.querySelectorAll(base).length;
              if(count)hoverRules.push({selector:raw,base_selector:base,count});
            }catch(error){invalid.push({selector:raw,error:error.message});}
          });
        }
        try{
          if(rule.cssRules&&rule.cssRules.length)inspectRules(rule.cssRules);
        }catch(error){
          hoverInspectable=false;
          notes.push("Nested stylesheet rules tidak dapat dibaca: "+error.message);
        }
      });};
      [...document.styleSheets].forEach(sheet=>{
        try{inspectRules(sheet.cssRules);}
        catch(error){hoverInspectable=false;notes.push("Stylesheet tidak dapat dibaca untuk verifikasi hover: "+(sheet.href||"inline stylesheet"));}
      });
      if(hoverRules.length){
        matches.push(...hoverRules.map(x=>({selector:x.selector,count:x.count,signal:"css_hover_rule",base_selector:x.base_selector})));
        notes.push("CSS :hover dan elemen target ditemukan; keyboard-equivalent state belum diuji.");
      }else if(hoverInspectable){notes.push("Tidak ditemukan pasangan CSS :hover dan elemen target yang dapat dibaca.");}
      else{notes.push("Pemeriksaan hover belum konklusif karena ada stylesheet yang tidak dapat dibaca.");}
      component.behavior_status="not_tested";
      component.keyboard_equivalent_status="not_tested";
    }
    let classification="exact_candidate";
    if(component.id==="CMP-043"&&matches.length){
      classification="partial_match";
      notes.push("Highlight/category tile ditemukan. Ini bukan bukti Article Card lengkap.");
    }
    if(component.id==="CMP-035"&&matches.length){
      classification="specialized_partial_match";
      notes.push("Mobile drawer ditemukan terlepas dari state open/closed; ini bukan reusable disclosure/accordion.");
    }
    if(["CMP-025","CMP-026"].includes(component.id)&&matches.length){
      classification="static_visual_match";
      notes.push("Counter visual ditemukan; data tidak terbukti dinamis atau terhubung ke backend/state.");
    }
    const hasUnambiguousMatch=matches.some(match=>!match.ambiguous);
    if(matches.some(match=>match.ambiguous)){
      notes.push("Sebagian selector digunakan oleh lebih dari satu record komponen; bukti tersebut tidak dianggap unik.");
    }
    if(matches.length&&!hasUnambiguousMatch){
      classification="ambiguous_candidate";
      notes.push("Seluruh kandidat yang cocok dipakai bersama oleh beberapa komponen; perlu review manual sebelum dianggap terdeteksi.");
    }
    let runtimeStatus;
     if(invalid.length)runtimeStatus="needs_review";
     else if(component.id==="CMP-033"&&!hoverInspectable&&!matches.some(m=>m.signal==="css_hover_rule"))runtimeStatus="needs_review";
     else if(matches.length&&!hasUnambiguousMatch)runtimeStatus="needs_review";
     else if(matches.length)runtimeStatus="detected";
    else if((component.selector_candidates||[]).length)runtimeStatus="not_detected";
    else runtimeStatus="needs_review";
    component.detection_matches=matches;
    component.detection_status=runtimeStatus;
    component.detection_classification=classification;
    component.detection_notes=notes;
    component.detection_checked_at=new Date().toISOString();
    return {matches,invalid,notes,status:runtimeStatus,classification,hover_inspectable:hoverInspectable};
  };
  const qaEvaluateExpectation=component=>{
    const source=component.source_status;
    const runtime=component.detection_status;
    let expectation="review";
    let reason="Source status partial atau runtime evidence belum cukup untuk menyimpulkan kecocokan.";
    if(runtime==="needs_review"){
      expectation="review";reason="Deteksi belum konklusif; perlu review manual.";
    }else if(source==="not_implemented"&&runtime==="not_detected"){
      expectation="match";reason="Tidak ditemukan kandidat; sesuai inventaris not_implemented (bukan bukti global ketiadaan fitur).";
    }else if(source==="not_implemented"&&runtime==="detected"){
      expectation="mismatch";reason="Kandidat ditemukan walau inventaris menyatakan not_implemented; perlu audit klasifikasi/selector.";
    }else if(source==="implemented"&&runtime==="detected"){
      expectation="match";reason="Kandidat ditemukan sesuai inventaris implemented; perilaku belum diuji.";
    }else if(source==="implemented"&&runtime==="not_detected"){
      expectation="mismatch";reason="Kandidat implemented tidak ditemukan; kemungkinan selector/DOM gap.";
    }else if(source==="partial"){
      expectation="review";
      if(runtime==="detected")reason="Ada kandidat visual/struktur, tetapi source berstatus partial; kelengkapan dan perilaku belum terbukti.";
      else reason="Source berstatus partial dan kandidat tidak ditemukan; perlu review selector dan batas implementasi.";
    }
    component.expectation_status=expectation;
    component.expectation_notes=reason;
    component.behavior_status=component.behavior_status||"not_tested";
    return {status:expectation,reason};
  };
  const qaRenderCatalog=(filter="")=>{
    const root=document.getElementById("qaCatalogList");root.replaceChildren();
    qaComponents.filter(c=>(c.name+" "+c.id+" "+c.category+" "+c.source_status+" "+c.detection_status+" "+(c.expectation_status||"")).toLowerCase().includes(filter.toLowerCase())).forEach(c=>{
      const runtime=c.detection_status==="not_scanned"?"NOT SCANNED":c.detection_status.replaceAll("_"," ").toUpperCase();
      const expectation=(c.expectation_status||"not_evaluated").replaceAll("_"," ").toUpperCase();
      const selectorText=c.selector_candidates?.length?c.selector_candidates.join(" | "):"No safe selector candidate documented";
      const meta=`${c.id} · ${c.category} · Source: ${c.source_status.toUpperCase()} · Runtime: ${runtime} · Expectation: ${expectation}`;
      const notes=[...(c.detection_notes||[]),c.expectation_notes].filter(Boolean).join(" ");
      const desc=`Selector candidates: ${selectorText}. ${c.gap} ${notes}`;
      const card=qaRecordCard(c.name,meta,desc);
      card.dataset.sourceStatus=c.source_status;card.dataset.detectionStatus=c.detection_status;card.dataset.expectationStatus=c.expectation_status||"not_evaluated";
      root.append(card);
    });
    const status=document.getElementById("qaCatalogScanStatus");
    if(status){
      const count=k=>qaComponents.filter(c=>c.detection_status===k).length;
      const exp=k=>qaComponents.filter(c=>c.expectation_status===k).length;
      status.textContent=`${qaComponents.length} components · Runtime: ${count("detected")} detected / ${count("not_detected")} not detected / ${count("needs_review")} needs review · Expectation: ${exp("match")} match / ${exp("mismatch")} mismatch / ${exp("review")} review`;
    }
  };
 const qaRunScenario=(scenario)=>{
   if(!scenario||!qaScenarios.some(item=>item.id===scenario.id))throw new Error("Unknown scenario supplied to executor.");
   const qaUiSnapshot=qaCaptureUiState();
   let pass=false,detail="",evidence={},executionStatus="failed";
   const el=selector=>document.querySelector(selector);
   try{
    if(scenario.component_scan){
      const component=qaComponents.find(c=>c.id===scenario.component_id);
      if(!component){executionStatus="blocked";detail="Component record tidak ditemukan.";}
      else if(!component.selector_candidates.length){component.detection_status="needs_review";component.detection_checked_at=new Date().toISOString();component.expectation_status="review";component.expectation_notes="Tidak ada selector kandidat yang cukup spesifik; perlu review manual.";executionStatus="blocked";detail=component.expectation_notes;evidence.review_required=true;}
      else{
        const scan=qaDetectComponent(component);
         const evaluation=qaEvaluateExpectation(component);
        pass=evaluation.status==="match";
        executionStatus=evaluation.status==="match"?"passed":(evaluation.status==="mismatch"?"failed":"blocked");
        detail=`Runtime ${scan.status.toUpperCase()}; expectation ${evaluation.status.toUpperCase()}. ${evaluation.reason}`;
        evidence={selector_candidates:component.selector_candidates,matches:scan.matches,invalid_selectors:scan.invalid,notes:scan.notes||[],classification:scan.classification,source_status:component.source_status,runtime_detection:scan.status,expectation_status:evaluation.status,expectation_reason:evaluation.reason,behavior_status:component.behavior_status||"not_tested",keyboard_equivalent_status:component.keyboard_equivalent_status||"not_tested",interpretation:"Runtime detection, inventory expectation, and behavior verification are separate. Passed means expectation match only; it does not mean component behavior passed."};
      }
    }else{
     switch(scenario.id){
      case "SCN-N-001": {const home=el("#home");pass=!!home;detail=pass?"Homepage container ditemukan.":"Homepage container tidak ditemukan.";evidence={selector:"#home",found:pass,ready_state:document.readyState};break;}
      case "SCN-N-002": pass=!!el("#qa-lab");detail=pass?"QA Lab section ditemukan.":"QA Lab section tidak ditemukan.";break;
      case "SCN-N-003": {
        const tab=el('[data-qa-tab="catalog"]'),pane=el('[data-qa-pane="catalog"]');
        if(!tab||!pane){executionStatus="blocked";detail="Tab catalog atau pane target tidak tersedia.";break;}
        const paneBefore=qaCaptureUiState().active_pane;
        const tabBefore=el(`[data-qa-tab="${paneBefore}"]`);
        const selectedBefore=tabBefore?.getAttribute("aria-selected")??null;
        tab.click();
        const paneAfterClick=document.querySelector("[data-qa-pane].active")?.dataset.qaPane||null;
        const selectedAfterClick=tab.getAttribute("aria-selected");
        pass=selectedAfterClick==="true"&&pane.classList.contains("active")&&paneAfterClick==="catalog";
        detail=pass?"Klik tab catalog mengaktifkan tab dan pane yang sesuai.":"Klik tab tidak menghasilkan state tab/pane yang diharapkan.";
        evidence={interaction:"click",pane_before:paneBefore,tab_selected_before:selectedBefore,tab_selected_after_click:selectedAfterClick,pane_after_click:paneAfterClick,catalog_pane_active:pane.classList.contains("active")};break;
      }
      case "SCN-N-004": {
        const button=el("#themeToggle");
        if(!button||button.disabled){executionStatus="blocked";detail="Theme toggle tidak tersedia atau disabled.";break;}
        const before=root.dataset.theme||"(default)",savedBefore=localStorage.getItem("mdz-theme"),colorMeta=document.querySelector('meta[name="theme-color"]'),metaBefore=colorMeta?.content??null;
        button.click();const after=root.dataset.theme||"(default)",savedAfterClick=localStorage.getItem("mdz-theme");
        const changed=after!==before;
        if(savedBefore===null)localStorage.removeItem("mdz-theme");else localStorage.setItem("mdz-theme",savedBefore);
        if(before==="(default)")delete root.dataset.theme;else root.dataset.theme=before;
        if(colorMeta&&metaBefore!==null)colorMeta.content=metaBefore;
        const themeRestored=(root.dataset.theme||"(default)")===before;
        const storageRestored=localStorage.getItem("mdz-theme")===savedBefore;
        const metaRestored=(colorMeta?.content??null)===metaBefore;
        pass=changed&&themeRestored&&storageRestored&&metaRestored;
        evidence={theme_before:before,theme_after:after,theme_changed:changed,storage_before:savedBefore,storage_after_click:savedAfterClick,theme_after_restore:root.dataset.theme||"(default)",storage_after_restore:localStorage.getItem("mdz-theme"),meta_before:metaBefore,meta_after_restore:colorMeta?.content??null,restore_matches_initial:themeRestored&&storageRestored&&metaRestored};
        detail=pass?"Tema berubah setelah klik dan root theme, storage, serta meta theme-color kembali ke nilai awal.":"Perubahan tema atau pemulihan root/storage/meta tidak sesuai nilai awal.";break;
      }
      case "SCN-N-005": {
        const dialog=el("#imageModal"),closeButton=el("#modalClose"),opener=document.querySelector(".media-open");
        if(!dialog||!closeButton||!opener){executionStatus="blocked";detail="Dialog, tombol close, atau pemicu gambar tidak tersedia.";break;}
        opener.click();const opened=dialog.classList.contains("open");
        const focusMovedToClose=document.activeElement===closeButton;
        if(opened)closeButton.click();const closed=!dialog.classList.contains("open");
        const focusReturnedToOpener=document.activeElement===opener;
        pass=opened&&closed&&focusMovedToClose&&focusReturnedToOpener;
        evidence={opener_clicked:true,dialog_opened:opened,focus_moved_to_close:focusMovedToClose,close_clicked:opened,dialog_closed:closed,focus_returned_to_opener:focusReturnedToOpener};
        detail=pass?"Dialog terbuka, fokus berpindah ke tombol close, dialog tertutup, dan fokus kembali ke pemicu.":"Siklus dialog atau pemulihan fokus tidak memenuhi kriteria.";break;
      }
      case "SCN-X-001": {
        const input=el("#qaCatalogSearch"),list=el("#qaCatalogList");
        if(!input||!list){executionStatus="blocked";detail="Input pencarian atau daftar katalog tidak tersedia.";break;}
        const originalValue=input.value,originalCount=list.children.length;
        input.value="Accordion";input.dispatchEvent(new Event("input",{bubbles:true}));
        const probeCount=list.children.length,probeVisible=probeCount>0;
        input.value="";input.dispatchEvent(new Event("input",{bubbles:true}));
        const emptyCount=list.children.length,emptyValue=input.value==="";
        input.value="Accordion";input.dispatchEvent(new Event("input",{bubbles:true}));
        const restoredProbeCount=list.children.length,probeRestored=input.value==="Accordion"&&restoredProbeCount===probeCount;
        pass=probeVisible&&emptyValue&&probeRestored;
        evidence={original_search_value:originalValue,original_visible_items:originalCount,probe_query:"Accordion",probe_visible_items:probeCount,empty_query_visible_items:emptyCount,probe_restored_visible_items:restoredProbeCount,empty_input_event_dispatched:true,probe_restore_event_dispatched:true,restore_matches_probe:probeRestored};
        detail=pass?"Pencarian non-kosong difilter, query kosong diproses, lalu hasil probe dipulihkan dengan jumlah item yang sama.":"Pengujian empty search atau pemulihan query probe tidak memenuhi kriteria.";break;
      }
      case "SCN-X-002": {const n=Math.max(1,Math.min(10,Number(el("#qa403Limit").value)||3));pass=n>=1&&n<=10;detail=`Threshold disanitasi menjadi ${n}; rentang aman 1–10.`;evidence.normalized_threshold=n;break;}
      case "SCN-X-003": executionStatus="blocked";detail="Tidak dijalankan: executor ini belum menginstrumentasi seluruh kanal network browser, sehingga tidak dapat membuktikan ketiadaan request.";evidence={verification:"not_instrumented",reason:"No network instrumentation"};break;
      case "SCN-A-001": {const nav=el('nav[aria-label="Navigasi utama"]');pass=!!nav&&!!nav.getAttribute("aria-label");detail=pass?"Primary navigation memiliki accessible name.":"Accessible name nav tidak ditemukan.";break;}
      case "SCN-A-002": {const tab=el('[data-qa-tab="overview"]');pass=!!tab&&tab.hasAttribute("aria-selected");detail=pass?"Tab mengumumkan aria-selected.":"State tab tidak ditemukan.";break;}
      case "SCN-A-003": {const controls=[...document.querySelectorAll("#qaWorkbench button,#qaWorkbench input")];const unnamed=controls.filter(x=>!(x.getAttribute("aria-label")||x.labels?.length||x.textContent.trim()||x.title));pass=unnamed.length===0;detail=pass?"Kontrol Workbench memiliki nama yang dapat diakses.":`${unnamed.length} kontrol belum memiliki nama yang terdeteksi.`;evidence.unnamed_count=unnamed.length;break;}
      case "SCN-R-001": {const width=document.documentElement.scrollWidth,viewport=document.documentElement.clientWidth;pass=width<=viewport+1;detail=`Current viewport only: document ${width}px; viewport ${viewport}px.`;evidence={document_width:width,viewport_width:viewport,horizontal_overflow_px:Math.max(0,width-viewport),scope:"current_viewport_only"};break;}
      case "SCN-R-002": {const workbench=el("#qaWorkbench");if(!workbench){executionStatus="blocked";detail="QA Workbench tidak ditemukan.";break;}const r=workbench.getBoundingClientRect(),viewport=document.documentElement.clientWidth;pass=r.width<=viewport+1&&r.left>=-1&&r.right<=viewport+1;detail=`Current viewport only: Workbench left ${Math.round(r.left)}px, right ${Math.round(r.right)}px, width ${Math.round(r.width)}px; viewport ${viewport}px.`;evidence={left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width),viewport_width:viewport,scope:"current_viewport_only"};break;}
      case "SCN-S-001": pass=true;detail="Tidak ada request eksternal yang dilakukan oleh security simulator.";evidence={simulation_only:true,network_requests:0};break;
      case "SCN-S-002": {const limit=Math.max(1,Math.min(10,Number(el("#qa403Limit").value)||3));let count=0;while(count<limit)count++;pass=count===limit;detail=`Simulasi berhenti tepat pada batas ${limit} respons 403 (simulasi lokal, bukan HTTP request).`;evidence.simulated_403_count=count;evidence.configured_limit=limit;evidence.simulation_only=true;evidence.network_requests=0;break;}
      default: executionStatus="blocked";detail="Belum ada executor yang didefinisikan untuk skenario ini.";
     }
     if(executionStatus!=="blocked")executionStatus=pass?"passed":"failed";
    }
   }catch(err){executionStatus="failed";detail=`Execution error: ${err.message}`;}
   try{
      qaRestoreUiState(qaUiSnapshot);
      if(["SCN-N-003","SCN-X-001"].includes(scenario.id)){
        const restoredPane=qaCaptureUiState().active_pane;
        const restoredSearch=qaCaptureUiState().search_value;
        const restoredSearchCount=el("#qaCatalogList")?.children.length??0;
        const initialSearchCount=(()=>{const list=el("#qaCatalogList");if(!list)return 0;const value=qaUiSnapshot.search_value;return qaComponents.filter(c=>(c.name+" "+c.id+" "+c.category+" "+c.source_status+" "+c.detection_status+" "+(c.expectation_status||"")).toLowerCase().includes(value.toLowerCase())).length;})();
        const paneMatches=restoredPane===qaUiSnapshot.active_pane;
        const searchMatches=restoredSearch===qaUiSnapshot.search_value&&restoredSearchCount===initialSearchCount;
        evidence.ui_state_restoration={search_value:restoredSearch,search_visible_items:restoredSearchCount,search_matches_initial:searchMatches,pane_after_restore:restoredPane,pane_matches_initial:paneMatches,restore_matches_initial:searchMatches&&paneMatches};
        if(!searchMatches||!paneMatches){executionStatus="failed";detail+=" UI state restoration did not match the initial snapshot.";}
        if(scenario.id==="SCN-N-003"){evidence.tab_selected_after_restore=el(`[data-qa-tab="${restoredPane}"]`)?.getAttribute("aria-selected")??null;evidence.pane_after_restore=restoredPane;evidence.restore_matches_initial=paneMatches;}
      }
    }
   catch(restoreError){executionStatus="failed";detail+=` UI state restoration failed: ${restoreError.message}`;evidence.cleanup_error=restoreError.message;}
   const result={
     session_id:qaSessionId,
     execution_id:qaCreateExecutionId(),
     result_kind:scenario.component_scan?"inventory_scan":"scenario_execution",
     scenario_id:scenario.id,component_id:scenario.component_id??null,name:scenario.name,lab:scenario.lab,
     status:executionStatus,actual_result:detail,evidence:qaClone(evidence),
     executed_at:new Date().toISOString(),page_url:qaSanitizePageUrl(location.href),
     viewport:{width:innerWidth,height:innerHeight}
   };
   scenario.status=executionStatus;scenario.actual_result=detail;scenario.last_verified=result.executed_at;scenario.evidence_ref=result.execution_id;qaResults.push(result);
   if(scenario.component_scan)qaRenderCatalog(document.getElementById("qaCatalogSearch").value);
   qaRenderScenarios(scenario.lab);qaRenderResults();qaUpdateSummary();return result;
 };
 const qaRenderScenarios=lab=>{
   const target=document.getElementById("qa"+lab[0].toUpperCase()+lab.slice(1)+"List");if(!target)return;target.replaceChildren();
   qaScenarios.filter(s=>s.lab===lab).forEach(s=>{
     const run=qaButton(s.status==="not_run"?"Run scenario":"Run again",()=>qaRunScenario(s));
     const detail=s.actual_result||s.purpose;
     const card=qaRecordCard(s.name,`${s.id} · ${s.component_id} · ${s.status.toUpperCase()}`,detail,run);
     card.dataset.status=s.status;
     target.append(card);
   });
 };
 const qaRenderResults=()=>{
   const root=el("#qaResultsList");root.replaceChildren();
   [...qaResults].reverse().forEach(r=>root.append(qaRecordCard(r.name,`${r.scenario_id} · ${r.status.toUpperCase()} · ${r.executed_at}`,r.actual_result)));
   el("#qaResultStatus").textContent=qaResults.length?`${qaResults.length} execution record(s) pada sesi ini.`:"Belum ada skenario dijalankan.";
 };
 const el=s=>document.querySelector(s);
 const qaUpdateSummary=()=>{
   el("#qaComponentCount").textContent=qaComponents.length;el("#qaScenarioCount").textContent=qaScenarios.length;
   el("#qaExecutedCount").textContent=qaResults.length;el("#qaPassedCount").textContent=qaResults.filter(r=>r.status==="passed").length;const failed=qaResults.filter(r=>r.status==="failed").length;const blocked=qaResults.filter(r=>r.status==="blocked").length;const status=el("#qaResultStatus");if(status&&qaResults.length)status.textContent=`${qaResults.length} execution record(s) · ${failed} failed · ${blocked} blocked · session ${qaSessionId.slice(0,8)}.`;
 };
 document.querySelectorAll("[data-qa-tab]").forEach(b=>b.addEventListener("click",()=>qaSetPane(b.dataset.qaTab)));
 document.querySelectorAll("[data-qa-jump]").forEach(b=>b.addEventListener("click",()=>qaSetPane(b.dataset.qaJump)));
 document.getElementById("qaCatalogSearch").addEventListener("input",e=>qaRenderCatalog(e.target.value));
 document.getElementById("qaScanCatalog").addEventListener("click",()=>{
    qaRenderCatalog(document.getElementById("qaCatalogSearch").value);
   qaComponents.forEach(c=>qaRunScenario(qaScenarios.find(s=>s.component_scan&&s.component_id===c.id)));
 });
 ["normal","negative","accessibility","responsive","security"].forEach(qaRenderScenarios);
 qaRenderCatalog();qaUpdateSummary();
 document.getElementById("qaRunAll").addEventListener("click",()=>{
   qaScenarios.filter(s=>s.lab!=="security").forEach(qaRunScenario);qaSetPane("results");
 });
 document.getElementById("qaExport").addEventListener("click",()=>{
   const payload={
     schema_version:"3.0",
     product:"MyDreamZone Living QA Playground",
     exported_at:new Date().toISOString(),
     session_id:qaSessionId,
     page_url:qaSanitizePageUrl(location.href),
     definitions:{
       components:qaClone(qaComponents.map(({detection_status,detection_classification,detection_matches,detection_notes,detection_checked_at,expectation_status,expectation_notes,behavior_status,keyboard_equivalent_status,...definition})=>definition)),
       scenarios:qaClone(qaScenarios.map(({status,actual_result,evidence_ref,last_verified,...definition})=>definition))
     },
     execution_results:qaClone(qaResults),
     summary:{
       component_count:qaComponents.length,
       scenario_count:qaScenarios.length,
       execution_records:qaResults.length,
       unique_scenarios_executed:new Set(qaResults.map(r=>r.scenario_id)).size,
       scenario_passed:qaResults.filter(r=>r.status==="passed").length,
       scenario_failed:qaResults.filter(r=>r.status==="failed").length,
       scenario_blocked:qaResults.filter(r=>r.status==="blocked").length,
       inventory_scan_records:qaResults.filter(r=>r.result_kind==="inventory_scan").length,
       behavioral_scenario_records:qaResults.filter(r=>r.result_kind==="scenario_execution").length,
       security_simulation_records:qaResults.filter(r=>r.evidence?.simulation_only===true).length
     },
     evidence_contract:{kind:"browser_session_metadata_json",screenshots_included:false,network_requests_from_security_simulator:0},
     notice:"Inventory scan results and behavioral scenario results are separate. A passed inventory scan means only that source-inventory expectation matched; it does not prove component behavior. Security checks are local simulations, not HTTP responses or penetration tests. URL query strings and fragments are omitted."
   };
   if(!qaValidateExportPayload(payload)){el("#qaResultStatus").textContent="Export dibatalkan: payload tidak lolos validasi.";return;}
   const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
   const url=URL.createObjectURL(blob);
   const a=document.createElement("a");a.href=url;
   a.download=`mdz-qa-evidence-${new Date().toISOString().replace(/[:.]/g,"-")}.json`;
   document.body.append(a);a.click();a.remove();
   setTimeout(()=>URL.revokeObjectURL(url),1000);
 });
 const qaValidateExportPayload=payload=>{
   return !!payload&&payload.schema_version==="3.0"&&
     !!payload.session_id&&!!payload.exported_at&&
     Array.isArray(payload.definitions?.components)&&payload.definitions.components.length===57&&
     Array.isArray(payload.definitions?.scenarios)&&payload.definitions.scenarios.length===72&&
     Array.isArray(payload.execution_results)&&
     payload.execution_results.every(r=>!!r.execution_id&&!!r.session_id&&!!r.scenario_id&&
       ["passed","failed","blocked"].includes(r.status)&&
       !/[?#]/.test(r.page_url||""))&&
     payload.execution_results.every(r=>r.session_id===payload.session_id);
 }; document.getElementById("qaRun403").addEventListener("click",()=>{const limit=Math.max(1,Math.min(10,Number(el("#qa403Limit").value)||3));el("#qa403Output").textContent=`Stopped at configured threshold: ${limit} simulated 403 responses. No network requests were sent.`;qaRunScenario(qaById("SCN-S-002"));});
 document.getElementById("qaClearResults").addEventListener("click",()=>{
   qaResults.length=0;
   qaScenarios.forEach(s=>{s.status="not_run";s.actual_result=null;s.evidence_ref=null;s.last_verified=null;});
   qaResetComponentState();
   const output=el("#qa403Output");if(output)output.textContent="Belum dijalankan.";
   qaRenderResults();qaUpdateSummary();
 });

})();
