(() => {
 const root=document.documentElement;
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
 document.addEventListener("keydown",e=>{if(e.key==="Escape"){close();document.getElementById("imageModal").classList.remove("open");}});
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
 document.querySelectorAll(".media-open").forEach(btn=>btn.addEventListener("click",()=>{modalImage.src=btn.dataset.image;modal.classList.add("open");}));
 document.getElementById("modalClose").addEventListener("click",()=>modal.classList.remove("open"));
 modal.addEventListener("click",e=>{if(e.target===modal)modal.classList.remove("open");});
 document.getElementById("backTop").addEventListener("click",()=>window.scrollTo({top:0,behavior:"smooth"}));
 const toast=document.getElementById("toast");let toastTimer;
 const showToast=msg=>{toast.textContent=msg;toast.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.classList.remove("show"),2200);};
 document.getElementById("watchTrailer").addEventListener("click",()=>showToast("Trailer MyDreamZone akan segera hadir."));
 document.getElementById("searchToggle").addEventListener("click",()=>showToast("Fitur pencarian akan dikembangkan pada tahap berikutnya."));
 document.getElementById("notificationToggle").addEventListener("click",()=>showToast("Belum ada notifikasi baru."));
})();