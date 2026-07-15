/* ============================================================
   静屿 — 音乐详情页（古琴五音）
   ============================================================ */

(function () {
  "use strict";

  const audio = document.getElementById("audio-player");
  if (!audio) return;

  const list = document.querySelectorAll(".song-item");
  const titleEl = document.querySelector(".player__title");
  const playBtn = document.querySelector(".player__btn--play");
  const prevBtn = document.querySelector(".player__btn--prev");
  const nextBtn = document.querySelector(".player__btn--next");
  const progressBar = document.querySelector(".player__bar");
  const progressFill = document.querySelector(".player__bar-fill");
  const currentTimeEl = document.querySelector(".player__time-current");
  const totalTimeEl = document.querySelector(".player__time-total");
  const volumeBar = document.querySelector(".player__volume-bar");
  const volumeFill = document.querySelector(".player__volume-fill");

  let currentIdx = -1;
  let reported = new Set();  // 已报告听完整曲

  function fmtTime(sec) {
    if (!isFinite(sec)) return "00:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function setActiveItem(idx) {
    list.forEach((el, i) => el.classList.toggle("is-playing", i === idx));
  }

  function playIndex(idx) {
    if (idx < 0 || idx >= list.length) return;
    currentIdx = idx;
    const item = list[idx];
    const url = item.dataset.audio;
    const title = item.dataset.title;
    const musicId = parseInt(item.dataset.id, 10);

    if (audio.src !== location.origin + url && !audio.src.endsWith(url)) {
      audio.src = url;
    }
    audio.play().catch(() => {});

    titleEl.textContent = title;
    setActiveItem(idx);
    playBtn.textContent = "⏸";

    // 重置上报
    reported = new Set();
  }

  function togglePlay() {
    if (currentIdx === -1 && list.length > 0) {
      playIndex(0);
      return;
    }
    if (audio.paused) {
      audio.play();
      playBtn.textContent = "⏸";
    } else {
      audio.pause();
      playBtn.textContent = "▶";
    }
  }

  // 列表点击
  list.forEach((item, idx) => {
    item.addEventListener("click", () => playIndex(idx));
  });

  // 播放/暂停
  playBtn.addEventListener("click", togglePlay);

  // 上一首 / 下一首
  prevBtn.addEventListener("click", () => {
    if (currentIdx > 0) playIndex(currentIdx - 1);
    else if (list.length > 0) playIndex(list.length - 1);
  });
  nextBtn.addEventListener("click", () => {
    if (currentIdx < list.length - 1) playIndex(currentIdx + 1);
    else if (list.length > 0) playIndex(0);
  });

  // 进度更新
  audio.addEventListener("timeupdate", () => {
    if (!audio.duration) return;
    const pct = (audio.currentTime / audio.duration) * 100;
    progressFill.style.width = pct + "%";
    currentTimeEl.textContent = fmtTime(audio.currentTime);
    totalTimeEl.textContent = fmtTime(audio.duration);

    // ≥ 90% 时调用 API 发放能量（每首只发一次）
    if (audio.currentTime / audio.duration >= 0.9) {
      const id = list[currentIdx]?.dataset.id;
      if (id && !reported.has(id)) {
        reported.add(id);
        const musicId = parseInt(id, 10);
        QI.fetchJSON("/api/music/listen-complete", {
          method: "POST",
          body: { music_id: musicId, progress: audio.currentTime / audio.duration },
        }).then((resp) => {
          if (resp?.granted) {
            QI.toast("+1 露水 💧", "success", 1600);
            QI.floatEnergy("+1 露水", list[currentIdx]);
            // 更新导航上的能量显示
            document.querySelectorAll("[data-energy-display]").forEach((el) => {
              el.textContent = resp.new_total_energy;
            });
          }
        }).catch(() => {});
      }
    }
  });

  // 进度条点击
  progressBar.addEventListener("click", (e) => {
    if (!audio.duration) return;
    const rect = progressBar.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    audio.currentTime = audio.duration * pct;
  });

  // 音量
  volumeBar.addEventListener("click", (e) => {
    const rect = volumeBar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    audio.volume = pct;
    volumeFill.style.width = (pct * 100) + "%";
  });

  // 结束自动下一首
  audio.addEventListener("ended", () => {
    if (currentIdx < list.length - 1) {
      playIndex(currentIdx + 1);
    } else {
      playBtn.textContent = "▶";
      setActiveItem(-1);
    }
  });

  // 初始化音量
  audio.volume = 0.8;
  volumeFill.style.width = "80%";
})();
