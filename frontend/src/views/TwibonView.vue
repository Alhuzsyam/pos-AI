<template>
  <!-- Wrapper: dark on mobile (story feel), normal on desktop -->
  <div :class="isMobile
    ? 'min-h-screen bg-gray-950 flex flex-col pb-[320px]'
    : 'p-4 md:p-6 min-h-full'">

    <!-- ══ DESKTOP HEADER ══ -->
    <div class="hidden lg:block mb-5">
      <h1 class="page-title">Twibon Maker</h1>
      <p class="page-subtitle">Buat frame foto Instagram Story • Ukuran 1080 × 1920 px</p>
    </div>

    <!-- ══ MOBILE HEADER (Instagram story style) ══ -->
    <div class="lg:hidden flex items-center justify-between px-4 py-3 border-b border-white/10">
      <span class="text-white font-semibold text-base tracking-tight">✨ Twibon Maker</span>
      <button @click="downloadTwibon" :disabled="downloading"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-full transition-colors disabled:opacity-50">
        {{ downloading ? '⏳' : '⬇️' }} Simpan
      </button>
    </div>

    <!-- ══ MAIN CONTENT ══ -->
    <div :class="isMobile ? 'flex flex-col items-center pt-3 px-3' : 'flex flex-col lg:flex-row gap-6 items-start'">

      <!-- ══════════════════════ LEFT PANEL (Desktop only) ══════════════════════ -->
      <div class="hidden lg:block w-full lg:w-80 flex-shrink-0 space-y-4">

        <!-- BACKGROUND -->
        <div class="card p-4">
          <h3 class="font-semibold text-sm text-claude-graphite mb-3">🎨 Background</h3>
          <div class="flex gap-2 mb-3">
            <Btn :active="bgType==='color'" @click="bgType='color'">🎨 Warna</Btn>
            <Btn :active="bgType==='photo'" @click="bgType='photo'">📷 Foto</Btn>
          </div>
          <div v-if="bgType==='color'" class="flex items-center gap-3">
            <input type="color" v-model="bgColor"
              class="w-12 h-10 rounded-lg cursor-pointer border border-claude-line p-0.5 bg-white" />
            <input type="text" v-model="bgColor"
              class="input flex-1 font-mono text-sm uppercase" placeholder="#c96442" />
          </div>
          <div v-else class="space-y-2">
            <label class="flex flex-col items-center justify-center border-2 border-dashed border-claude-line rounded-xl p-4 cursor-pointer hover:bg-claude-surface transition-colors">
              <span class="text-2xl mb-1">📁</span>
              <span class="text-xs text-claude-dust text-center">
                {{ bgPhotoImg ? 'Ganti foto background' : 'Upload foto background' }}
              </span>
              <input type="file" accept="image/*" class="hidden" @change="onBgPhotoChange" />
            </label>
            <div v-if="bgPhotoImg" class="space-y-2">
              <SliderRow label="Skala" :display="bgPhotoScale.toFixed(2)+'x'"
                v-model="bgPhotoScale" min="0.5" max="4" step="0.05" />
              <div class="grid grid-cols-2 gap-2">
                <SliderRow label="Offset X" :display="Math.round(bgPhotoOffsetX*100)+'%'"
                  v-model="bgPhotoOffsetX" min="0" max="1" step="0.01" />
                <SliderRow label="Offset Y" :display="Math.round(bgPhotoOffsetY*100)+'%'"
                  v-model="bgPhotoOffsetY" min="0" max="1" step="0.01" />
              </div>
            </div>
          </div>
        </div>

        <!-- ASSETS -->
        <div class="card p-4">
          <h3 class="font-semibold text-sm text-claude-graphite mb-3">🖼️ Assets / Gambar</h3>
          <div class="mb-4">
            <div class="flex items-center justify-between mb-2">
              <p class="text-xs text-claude-dust font-medium">Library</p>
              <label class="flex items-center gap-1 px-2.5 py-1 bg-brand-500 text-white text-xs font-medium rounded-md cursor-pointer hover:bg-brand-600 transition-colors">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
                </svg>
                Upload
                <input type="file" accept="image/*" multiple class="hidden" @change="onAssetUpload" />
              </label>
            </div>
            <div v-if="assetLibrary.length === 0" class="text-center py-4 text-xs text-claude-dust">
              <span class="text-2xl block mb-1">🖼️</span>Memuat assets...
            </div>
            <div v-else class="grid grid-cols-4 gap-1.5 max-h-44 overflow-y-auto pr-0.5">
              <button v-for="a in assetLibrary" :key="a.id"
                @click="addLayer(a)" :disabled="!a.img" :title="a.name + ' — klik untuk tambahkan'"
                class="aspect-square rounded-lg border border-claude-line overflow-hidden hover:border-brand-400 hover:shadow-md transition-all disabled:opacity-40 bg-claude-surface">
                <img :src="a.url" :alt="a.name" class="w-full h-full object-contain p-0.5" />
              </button>
            </div>
            <p class="text-xs text-claude-dust mt-1.5 text-center">Klik gambar untuk letakkan di canvas</p>
          </div>

          <div class="border-t border-claude-line pt-3">
            <p class="text-xs font-medium text-claude-graphite mb-2">
              Lapisan Gambar
              <span class="ml-1 px-1.5 py-0.5 bg-claude-surface text-claude-dust rounded-full text-xs font-normal">{{ layers.length }}</span>
            </p>
            <div v-if="layers.length === 0" class="text-center py-3 text-xs text-claude-dust">
              Belum ada gambar. Klik dari library di atas.
            </div>
            <div v-else class="space-y-1 mb-2">
              <div v-for="(l, i) in [...layers].reverse()" :key="l.id"
                @click="selectLayer(layers.length - 1 - i)"
                :class="['flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors',
                  selectedLayerIdx === layers.length - 1 - i
                    ? 'bg-brand-50 border border-brand-200'
                    : 'hover:bg-claude-surface border border-transparent']">
                <img :src="l.url" class="w-8 h-8 object-contain rounded flex-shrink-0 bg-claude-surface border border-claude-line" />
                <span class="flex-1 truncate text-xs font-medium text-claude-graphite">{{ l.name }}</span>
                <div class="flex items-center gap-0.5 flex-shrink-0">
                  <button @click.stop="moveLayerUp(layers.length - 1 - i)"
                    :disabled="layers.length - 1 - i >= layers.length - 1"
                    class="p-1 text-claude-dust hover:text-claude-graphite disabled:opacity-30 transition-colors">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7"/></svg>
                  </button>
                  <button @click.stop="moveLayerDown(layers.length - 1 - i)"
                    :disabled="layers.length - 1 - i <= 0"
                    class="p-1 text-claude-dust hover:text-claude-graphite disabled:opacity-30 transition-colors">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/></svg>
                  </button>
                  <button @click.stop="removeLayer(layers.length - 1 - i)"
                    class="p-1 text-red-400 hover:text-red-600 transition-colors">
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                  </button>
                </div>
              </div>
            </div>
            <Transition name="slide-fade">
              <div v-if="selectedLayerIdx >= 0 && layers[selectedLayerIdx]"
                class="border-t border-claude-line pt-3 space-y-2 mt-1">
                <p class="text-xs font-medium text-claude-graphite">
                  Edit: <span class="text-brand-600">{{ layers[selectedLayerIdx].name }}</span>
                </p>
                <SliderRow label="Ukuran (skala)"
                  :display="layers[selectedLayerIdx].scale.toFixed(2)+'x'"
                  v-model="layers[selectedLayerIdx].scale" min="0.02" max="5" step="0.01" />
                <div class="grid grid-cols-2 gap-2">
                  <SliderRow label="Posisi X"
                    :display="Math.round(layers[selectedLayerIdx].x*100)+'%'"
                    v-model="layers[selectedLayerIdx].x" min="-0.5" max="1.5" step="0.005" />
                  <SliderRow label="Posisi Y"
                    :display="Math.round(layers[selectedLayerIdx].y*100)+'%'"
                    v-model="layers[selectedLayerIdx].y" min="-0.5" max="1.5" step="0.005" />
                </div>
                <button @click="resetLayer(selectedLayerIdx)"
                  class="w-full py-1.5 text-xs text-claude-dust hover:text-claude-graphite border border-claude-line rounded-md transition-colors">
                  ↺ Reset posisi &amp; ukuran
                </button>
              </div>
            </Transition>
          </div>
        </div>

        <!-- TEXT LAYERS -->
        <div class="card p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-sm text-claude-graphite">✍️ Teks</h3>
            <button @click="addText"
              class="px-3 py-1.5 bg-brand-500 text-white text-xs font-medium rounded-md hover:bg-brand-600 transition-colors">
              + Tambah
            </button>
          </div>
          <div v-if="texts.length === 0" class="text-center py-4 text-xs text-claude-dust">
            Belum ada teks. Klik "+ Tambah".
          </div>
          <div v-else class="space-y-1 mb-3">
            <div v-for="(t, i) in texts" :key="t.id"
              @click="selectedTextIdx = i; selectedLayerIdx = -1"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors text-xs',
                selectedTextIdx === i ? 'bg-brand-50 border border-brand-200 text-claude-ink' : 'hover:bg-claude-surface text-claude-slate border border-transparent']">
              <span class="flex-1 truncate font-medium">{{ t.content || '(kosong)' }}</span>
              <button @click.stop="removeText(i)" class="text-red-400 hover:text-red-600 transition-colors flex-shrink-0">✕</button>
            </div>
          </div>
          <Transition name="slide-fade">
            <div v-if="selectedTextIdx >= 0 && texts[selectedTextIdx]"
              class="border-t border-claude-line pt-3 space-y-3">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <label class="label text-xs">Isi teks</label>
                  <button @click="showEmojiPicker = !showEmojiPicker"
                    class="text-lg leading-none hover:scale-110 transition-transform" title="Tambah emoji">😊</button>
                </div>
                <div v-if="showEmojiPicker" class="mb-2 p-2 bg-claude-surface rounded-xl border border-claude-line">
                  <div class="grid grid-cols-8 gap-1 max-h-28 overflow-y-auto">
                    <button v-for="em in emojis" :key="em" @click="insertEmoji(em)"
                      class="text-lg hover:bg-white rounded-lg p-0.5 transition-colors leading-none">{{ em }}</button>
                  </div>
                </div>
                <textarea v-model="texts[selectedTextIdx].content"
                  class="input text-sm mt-1 resize-none h-16 leading-relaxed"
                  placeholder="Ketik teks di sini..." />
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="label text-xs">Ukuran font (px)</label>
                  <input type="number" v-model.number="texts[selectedTextIdx].fontSize"
                    min="10" max="400" class="input text-sm mt-1" />
                  <p class="text-xs text-claude-dust mt-0.5">di 1080px</p>
                </div>
                <div>
                  <label class="label text-xs">Warna</label>
                  <div class="flex gap-2 mt-1">
                    <input type="color" v-model="texts[selectedTextIdx].color"
                      class="w-9 h-9 rounded-lg cursor-pointer border border-claude-line p-0.5 bg-white" />
                    <input type="text" v-model="texts[selectedTextIdx].color"
                      class="input flex-1 font-mono text-xs" />
                  </div>
                </div>
              </div>
              <div>
                <label class="label text-xs">Font</label>
                <select v-model="texts[selectedTextIdx].fontFamily" class="input text-sm mt-1">
                  <option value="Arial">Arial</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Impact">Impact</option>
                  <option value="Times New Roman">Times New Roman</option>
                  <option value="Trebuchet MS">Trebuchet MS</option>
                  <option value="Verdana">Verdana</option>
                  <option value="Courier New">Courier New</option>
                </select>
              </div>
              <div class="flex gap-2">
                <ToggleBtn v-model="texts[selectedTextIdx].fontWeight" on-val="bold" off-val="normal">
                  <b>B</b> Bold
                </ToggleBtn>
                <ToggleBtn v-model="texts[selectedTextIdx].italic">
                  <i>I</i> Italic
                </ToggleBtn>
                <ToggleBtn v-model="texts[selectedTextIdx].shadow">Shadow</ToggleBtn>
              </div>
              <div>
                <label class="label text-xs mb-1">Rata teks</label>
                <div class="flex gap-1">
                  <button v-for="al in ['left','center','right']" :key="al"
                    @click="texts[selectedTextIdx].textAlign = al"
                    :class="['flex-1 py-1.5 rounded-md text-xs transition-colors border',
                      texts[selectedTextIdx].textAlign === al ? 'bg-brand-500 text-white border-brand-500' : 'bg-claude-surface text-claude-slate border-claude-line']">
                    {{ al === 'left' ? '◀' : al === 'center' ? '▬' : '▶' }} {{ al }}
                  </button>
                </div>
              </div>
              <div>
                <label class="label text-xs">Posisi (atau drag di canvas)</label>
                <div class="grid grid-cols-2 gap-2 mt-1">
                  <SliderRow label="X" :display="Math.round(texts[selectedTextIdx].x*100)+'%'"
                    v-model="texts[selectedTextIdx].x" min="0" max="1" step="0.005" />
                  <SliderRow label="Y" :display="Math.round(texts[selectedTextIdx].y*100)+'%'"
                    v-model="texts[selectedTextIdx].y" min="0" max="1" step="0.005" />
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- DOWNLOAD (desktop) -->
        <button @click="downloadTwibon" :disabled="downloading"
          class="w-full py-3 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-colors shadow-sm">
          {{ downloading ? '⏳ Menyiapkan...' : '⬇️ Download PNG  (1080 × 1920)' }}
        </button>
      </div>

      <!-- ══════════════════════ CANVAS ═════════════════════════ -->
      <div :class="isMobile
        ? 'w-full flex flex-col items-center'
        : 'flex-1 flex flex-col items-center sticky top-6'">
        <p class="hidden lg:block text-xs text-claude-dust mb-2">Preview Instagram Story</p>
        <div class="relative rounded-xl overflow-hidden shadow-xl"
          :class="isMobile ? 'border-0 shadow-2xl' : 'border border-claude-line'"
          :style="{ width: DISPLAY_W + 'px', maxWidth: '100%' }">
          <canvas ref="previewCanvas" :width="DISPLAY_W" :height="DISPLAY_H"
            :class="['block w-full h-auto select-none', cursorClass]"
            @mousedown="onMouseDown" @mousemove="onMouseMove"
            @mouseup="onMouseUp" @mouseleave="onMouseLeave"
            @touchstart.prevent="onTouchStart" @touchmove.prevent="onTouchMove"
            @touchend.prevent="onTouchEnd" />
        </div>
        <p class="hidden lg:block text-xs text-claude-dust mt-2">{{ DISPLAY_W }}×{{ DISPLAY_H }}px → Export 1080×1920px</p>
        <div class="hidden lg:flex gap-2 mt-3 flex-wrap justify-center">
          <span class="px-2 py-1 bg-claude-surface text-claude-dust text-xs rounded-full border border-claude-line">🖱️ Drag gambar/teks pindah</span>
          <span class="px-2 py-1 bg-claude-surface text-claude-dust text-xs rounded-full border border-claude-line">🔵 Sudut biru = resize</span>
          <span class="px-2 py-1 bg-claude-surface text-claude-dust text-xs rounded-full border border-claude-line">↑↓ Atur urutan layer</span>
        </div>
        <!-- Mobile hint -->
        <p v-if="isMobile" class="text-white/40 text-xs mt-2">👆 Drag gambar/teks di canvas untuk memindahkan</p>
      </div>

    </div>

    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- MOBILE BOTTOM CONTROLS (Instagram story feel)             -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <div class="lg:hidden fixed bottom-0 left-0 right-0 z-50">

      <!-- Tab bar -->
      <div class="flex bg-gray-900/95 backdrop-blur-md border-t border-white/10">
        <button v-for="tab in mobileTabs" :key="tab.id"
          @click="activeTab = tab.id"
          :class="['flex-1 flex flex-col items-center gap-0.5 py-2.5 text-xs font-medium transition-colors',
            activeTab === tab.id ? 'text-white' : 'text-white/40']">
          <span class="text-xl leading-none">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
          <div v-if="activeTab === tab.id" class="w-4 h-0.5 bg-white rounded-full mt-0.5"></div>
        </button>
      </div>

      <!-- Panel content -->
      <div class="bg-gray-900/95 backdrop-blur-md border-t border-white/10 max-h-64 overflow-y-auto">

        <!-- 🎨 BACKGROUND TAB -->
        <div v-if="activeTab === 'bg'" class="p-4 space-y-3">
          <div class="flex gap-2">
            <button @click="bgType='color'"
              :class="['flex-1 py-2 rounded-xl text-xs font-semibold transition-colors',
                bgType==='color' ? 'bg-white text-gray-900' : 'bg-white/10 text-white/70']">
              🎨 Warna
            </button>
            <button @click="bgType='photo'"
              :class="['flex-1 py-2 rounded-xl text-xs font-semibold transition-colors',
                bgType==='photo' ? 'bg-white text-gray-900' : 'bg-white/10 text-white/70']">
              📷 Foto
            </button>
          </div>
          <div v-if="bgType==='color'" class="flex items-center gap-3">
            <input type="color" v-model="bgColor"
              class="w-12 h-10 rounded-xl cursor-pointer border-0 p-0 bg-transparent" />
            <input type="text" v-model="bgColor"
              class="flex-1 bg-white/10 text-white font-mono text-sm uppercase rounded-xl px-3 py-2 border border-white/20 focus:outline-none focus:border-white/50" placeholder="#c96442" />
          </div>
          <div v-else class="space-y-2">
            <label class="flex flex-col items-center justify-center border-2 border-dashed border-white/20 rounded-xl p-4 cursor-pointer hover:bg-white/5 transition-colors">
              <span class="text-2xl mb-1">📁</span>
              <span class="text-xs text-white/60 text-center">
                {{ bgPhotoImg ? '🔄 Ganti foto background' : '📤 Upload foto background' }}
              </span>
              <input type="file" accept="image/*" class="hidden" @change="onBgPhotoChange" />
            </label>
            <div v-if="bgPhotoImg" class="space-y-2">
              <MobileSlider label="Skala" :display="bgPhotoScale.toFixed(2)+'x'"
                v-model="bgPhotoScale" min="0.5" max="4" step="0.05" />
              <div class="grid grid-cols-2 gap-2">
                <MobileSlider label="Offset X" :display="Math.round(bgPhotoOffsetX*100)+'%'"
                  v-model="bgPhotoOffsetX" min="0" max="1" step="0.01" />
                <MobileSlider label="Offset Y" :display="Math.round(bgPhotoOffsetY*100)+'%'"
                  v-model="bgPhotoOffsetY" min="0" max="1" step="0.01" />
              </div>
            </div>
          </div>
        </div>

        <!-- 🖼️ ASSETS TAB -->
        <div v-if="activeTab === 'assets'" class="p-4 space-y-3">
          <div class="flex items-center justify-between">
            <p class="text-white/60 text-xs font-medium">Library Assets</p>
            <label class="flex items-center gap-1 px-3 py-1.5 bg-white/15 text-white text-xs font-medium rounded-full cursor-pointer hover:bg-white/25 transition-colors">
              ➕ Upload
              <input type="file" accept="image/*" multiple class="hidden" @change="onAssetUpload" />
            </label>
          </div>
          <div v-if="assetLibrary.length === 0" class="text-center py-4 text-xs text-white/40">
            <span class="text-2xl block mb-1">🖼️</span>Memuat assets...
          </div>
          <div v-else class="grid grid-cols-5 gap-2">
            <button v-for="a in assetLibrary" :key="a.id"
              @click="addLayer(a)" :disabled="!a.img"
              class="aspect-square rounded-xl border border-white/20 overflow-hidden hover:border-white/60 hover:shadow-lg transition-all disabled:opacity-40 bg-white/5">
              <img :src="a.url" :alt="a.name" class="w-full h-full object-contain p-1" />
            </button>
          </div>

          <!-- Placed layers on mobile -->
          <div v-if="layers.length > 0" class="border-t border-white/10 pt-3">
            <p class="text-white/60 text-xs font-medium mb-2">
              Lapisan aktif
              <span class="ml-1 px-1.5 py-0.5 bg-white/10 text-white/50 rounded-full text-xs">{{ layers.length }}</span>
            </p>
            <div class="space-y-1.5">
              <div v-for="(l, i) in [...layers].reverse()" :key="l.id"
                @click="selectLayer(layers.length - 1 - i)"
                :class="['flex items-center gap-2 px-3 py-2 rounded-xl cursor-pointer transition-colors',
                  selectedLayerIdx === layers.length - 1 - i
                    ? 'bg-white/20 border border-white/30'
                    : 'bg-white/5 border border-white/10']">
                <img :src="l.url" class="w-8 h-8 object-contain rounded-lg flex-shrink-0 bg-white/10" />
                <span class="flex-1 truncate text-xs font-medium text-white">{{ l.name }}</span>
                <button @click.stop="removeLayer(layers.length - 1 - i)"
                  class="text-red-400 hover:text-red-300 transition-colors text-sm">✕</button>
              </div>
            </div>
            <!-- Selected layer controls -->
            <div v-if="selectedLayerIdx >= 0 && layers[selectedLayerIdx]" class="mt-3 space-y-2">
              <MobileSlider label="Ukuran"
                :display="layers[selectedLayerIdx].scale.toFixed(2)+'x'"
                v-model="layers[selectedLayerIdx].scale" min="0.02" max="5" step="0.01" />
            </div>
          </div>
        </div>

        <!-- ✍️ TEXT TAB -->
        <div v-if="activeTab === 'text'" class="p-4 space-y-3">
          <div class="flex items-center justify-between">
            <p class="text-white/60 text-xs font-medium">Layer Teks</p>
            <button @click="addText"
              class="px-3 py-1.5 bg-white/15 text-white text-xs font-semibold rounded-full hover:bg-white/25 transition-colors">
              ✍️ + Tambah
            </button>
          </div>

          <div v-if="texts.length === 0" class="text-center py-4 text-xs text-white/40">
            Belum ada teks. Klik "+ Tambah".
          </div>
          <div v-else class="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            <button v-for="(t, i) in texts" :key="t.id"
              @click="selectedTextIdx = i; selectedLayerIdx = -1"
              :class="['flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
                selectedTextIdx === i ? 'bg-white text-gray-900' : 'bg-white/10 text-white/70']">
              <span class="max-w-[80px] truncate">{{ t.content || '(kosong)' }}</span>
              <span @click.stop="removeText(i)" class="text-red-400 hover:text-red-300 ml-0.5">✕</span>
            </button>
          </div>

          <!-- Selected text editor (mobile) -->
          <Transition name="slide-fade">
            <div v-if="selectedTextIdx >= 0 && texts[selectedTextIdx]" class="space-y-3">
              <!-- Text input + emoji -->
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <span class="text-white/60 text-xs">Isi teks</span>
                  <button @click="showEmojiPicker = !showEmojiPicker"
                    :class="['text-xl leading-none transition-transform hover:scale-110', showEmojiPicker ? 'scale-110' : '']">😊</button>
                </div>
                <!-- Emoji picker -->
                <Transition name="slide-fade">
                  <div v-if="showEmojiPicker" class="mb-2 p-2 bg-black/50 rounded-2xl border border-white/10">
                    <div class="grid grid-cols-8 gap-1 max-h-24 overflow-y-auto">
                      <button v-for="em in emojis" :key="em" @click="insertEmoji(em)"
                        class="text-xl hover:bg-white/10 rounded-lg p-0.5 transition-colors leading-none">{{ em }}</button>
                    </div>
                  </div>
                </Transition>
                <textarea v-model="texts[selectedTextIdx].content"
                  class="w-full bg-white/10 text-white text-sm rounded-xl px-3 py-2.5 border border-white/20 focus:outline-none focus:border-white/50 resize-none h-16 leading-relaxed placeholder:text-white/30"
                  placeholder="Ketik teks di sini..." />
              </div>

              <!-- Font size + color -->
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="text-white/50 text-xs block mb-1">Ukuran font</label>
                  <input type="number" v-model.number="texts[selectedTextIdx].fontSize"
                    min="10" max="400"
                    class="w-full bg-white/10 text-white text-sm rounded-xl px-3 py-2 border border-white/20 focus:outline-none focus:border-white/50" />
                </div>
                <div>
                  <label class="text-white/50 text-xs block mb-1">Warna</label>
                  <div class="flex gap-2">
                    <input type="color" v-model="texts[selectedTextIdx].color"
                      class="w-10 h-10 rounded-xl cursor-pointer border-0 p-0 bg-transparent" />
                    <input type="text" v-model="texts[selectedTextIdx].color"
                      class="flex-1 bg-white/10 text-white font-mono text-xs rounded-xl px-2 border border-white/20 focus:outline-none" />
                  </div>
                </div>
              </div>

              <!-- Style toggles -->
              <div class="flex gap-2">
                <button @click="texts[selectedTextIdx].fontWeight = texts[selectedTextIdx].fontWeight === 'bold' ? 'normal' : 'bold'"
                  :class="['flex-1 py-2 rounded-xl text-xs font-semibold transition-colors border',
                    texts[selectedTextIdx].fontWeight === 'bold' ? 'bg-white text-gray-900 border-white' : 'bg-white/10 text-white/70 border-white/20']">
                  <b>B</b> Bold
                </button>
                <button @click="texts[selectedTextIdx].italic = !texts[selectedTextIdx].italic"
                  :class="['flex-1 py-2 rounded-xl text-xs font-semibold transition-colors border',
                    texts[selectedTextIdx].italic ? 'bg-white text-gray-900 border-white' : 'bg-white/10 text-white/70 border-white/20']">
                  <i>I</i> Italic
                </button>
                <button @click="texts[selectedTextIdx].shadow = !texts[selectedTextIdx].shadow"
                  :class="['flex-1 py-2 rounded-xl text-xs font-semibold transition-colors border',
                    texts[selectedTextIdx].shadow ? 'bg-white text-gray-900 border-white' : 'bg-white/10 text-white/70 border-white/20']">
                  💡 Shadow
                </button>
              </div>

              <!-- Align -->
              <div class="flex gap-2">
                <button v-for="al in ['left','center','right']" :key="al"
                  @click="texts[selectedTextIdx].textAlign = al"
                  :class="['flex-1 py-2 rounded-xl text-xs transition-colors border',
                    texts[selectedTextIdx].textAlign === al ? 'bg-white text-gray-900 border-white' : 'bg-white/10 text-white/70 border-white/20']">
                  {{ al === 'left' ? '◀ Kiri' : al === 'center' ? '▬ Tengah' : '▶ Kanan' }}
                </button>
              </div>

              <!-- Position sliders -->
              <div class="grid grid-cols-2 gap-2">
                <MobileSlider label="Posisi X" :display="Math.round(texts[selectedTextIdx].x*100)+'%'"
                  v-model="texts[selectedTextIdx].x" min="0" max="1" step="0.005" />
                <MobileSlider label="Posisi Y" :display="Math.round(texts[selectedTextIdx].y*100)+'%'"
                  v-model="texts[selectedTextIdx].y" min="0" max="1" step="0.005" />
              </div>
            </div>
          </Transition>
        </div>

      </div>
    </div>
    <!-- END MOBILE CONTROLS -->

  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick, h, defineComponent } from 'vue'

// ── Mini components (Desktop) ──────────────────────────────────────────────
const SliderRow = defineComponent({
  props: ['label','display','modelValue','min','max','step'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('div', [
      h('div', { class: 'flex justify-between mb-1' }, [
        h('span', { class: 'text-xs text-claude-dust' }, props.label),
        h('span', { class: 'text-xs font-mono text-claude-graphite' }, props.display),
      ]),
      h('input', {
        type: 'range', value: props.modelValue,
        min: props.min, max: props.max, step: props.step,
        class: 'w-full accent-brand-500',
        onInput: e => emit('update:modelValue', +e.target.value),
      })
    ])
  }
})

// ── Mini components (Mobile dark) ──────────────────────────────────────────
const MobileSlider = defineComponent({
  props: ['label','display','modelValue','min','max','step'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () => h('div', [
      h('div', { class: 'flex justify-between mb-1' }, [
        h('span', { class: 'text-xs text-white/50' }, props.label),
        h('span', { class: 'text-xs font-mono text-white/80' }, props.display),
      ]),
      h('input', {
        type: 'range', value: props.modelValue,
        min: props.min, max: props.max, step: props.step,
        class: 'w-full accent-white',
        onInput: e => emit('update:modelValue', +e.target.value),
      })
    ])
  }
})

const Btn = defineComponent({
  props: ['active'],
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () => h('button', {
      class: ['flex-1 py-1.5 px-3 rounded-md text-xs font-medium transition-colors border',
        props.active ? 'bg-brand-500 text-white border-brand-500' : 'bg-claude-surface text-claude-slate border-claude-line hover:bg-claude-paper'].join(' '),
      onClick: e => emit('click', e),
    }, slots.default?.())
  }
})

const ToggleBtn = defineComponent({
  props: { modelValue: {}, onVal: { default: true }, offVal: { default: false } },
  emits: ['update:modelValue'],
  setup(props, { slots, emit }) {
    const active = computed(() => props.modelValue === props.onVal || (props.onVal === true && !!props.modelValue))
    return () => h('button', {
      class: ['flex-1 py-1.5 rounded-md text-xs transition-colors border',
        active.value ? 'bg-brand-500 text-white border-brand-500' : 'bg-claude-surface text-claude-slate border-claude-line'].join(' '),
      onClick: () => {
        if (props.onVal === true) emit('update:modelValue', !props.modelValue)
        else emit('update:modelValue', active.value ? props.offVal : props.onVal)
      },
    }, slots.default?.())
  }
})

// ── Canvas dimensions ──────────────────────────────────────────────────────
const CANVAS_W  = 1080
const CANVAS_H  = 1920
const DISPLAY_W = 300
const DISPLAY_H = Math.round(DISPLAY_W * CANVAS_H / CANVAS_W)

// ── Mobile layout state ────────────────────────────────────────────────────
const windowWidth = ref(window.innerWidth)
const isMobile    = computed(() => windowWidth.value < 1024)
const activeTab   = ref('bg')

const mobileTabs = [
  { id: 'bg',     icon: '🎨', label: 'Background' },
  { id: 'assets', icon: '🖼️', label: 'Gambar'     },
  { id: 'text',   icon: '✍️',  label: 'Teks'       },
]

function onResize() { windowWidth.value = window.innerWidth }

// ── Emoji picker ───────────────────────────────────────────────────────────
const showEmojiPicker = ref(false)
const emojis = [
  '😊','😍','🔥','💥','✨','🎉','👑','💪','🙏','❤️',
  '💕','🌟','⭐','🏆','🎯','💯','🙌','👏','🤩','😎',
  '🌈','🦋','🌺','🌸','💐','🍀','🎊','🎁','📸','💫',
  '⚡','🌙','☀️','🎶','🎵','💃','🕺','🤳','📱','💬',
  '🫶','🥰','😘','🤑','🎀','🪄','🦄','🍕','🧋','🌮',
]

function insertEmoji(emoji) {
  if (selectedTextIdx.value >= 0 && texts.value[selectedTextIdx.value]) {
    texts.value[selectedTextIdx.value].content += emoji
    showEmojiPicker.value = false
  }
}

// ── Background ─────────────────────────────────────────────────────────────
const bgType         = ref('color')
const bgColor        = ref('#c96442')
const bgPhotoImg     = ref(null)
const bgPhotoScale   = ref(1.0)
const bgPhotoOffsetX = ref(0.5)
const bgPhotoOffsetY = ref(0.5)

// ── Asset library ──────────────────────────────────────────────────────────
let assetIdSeq = 0
const assetLibrary = ref([])

// ── Canvas layers ──────────────────────────────────────────────────────────
let layerIdSeq = 0
const layers           = ref([])
const selectedLayerIdx = ref(-1)

// ── Texts ──────────────────────────────────────────────────────────────────
let textIdSeq = 0
const texts         = ref([])
const selectedTextIdx = ref(-1)

// ── Canvas ref ─────────────────────────────────────────────────────────────
const previewCanvas = ref(null)
const downloading   = ref(false)

// ── Drag state ─────────────────────────────────────────────────────────────
const dragMode         = ref(null)
const dragging         = ref(false)
const dragLayerIdx     = ref(-1)
const dragTextIdx      = ref(-1)
const dragOffX         = ref(0)
const dragOffY         = ref(0)
const resizeStartScale = ref(1)
const resizeStartDist  = ref(100)
const hoverMode        = ref(null)

const HANDLE_R = 8

const cursorClass = computed(() => {
  if (dragging.value) return 'cursor-grabbing'
  if (hoverMode.value === 'layer-resize') return 'cursor-nwse-resize'
  if (hoverMode.value === 'layer' || hoverMode.value === 'text') return 'cursor-grab'
  return 'cursor-crosshair'
})

// ── Load default assets ────────────────────────────────────────────────────
const rawAssets = import.meta.glob('@/images/*.png', { eager: true, as: 'url' })

onMounted(async () => {
  window.addEventListener('resize', onResize)
  const entries = Object.entries(rawAssets).sort(([a], [b]) => a.localeCompare(b))
  for (const [path, url] of entries) {
    const name = path.split('/').pop().replace(/\.png$/i, '')
    const item = reactive({ id: ++assetIdSeq, name, url, img: null })
    assetLibrary.value.push(item)
    const img = new Image()
    img.onload = () => { item.img = img; redraw() }
    img.src = url
  }
  await nextTick()
  redraw()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

// ── Asset upload ───────────────────────────────────────────────────────────
function onAssetUpload(e) {
  const files = [...(e.target.files || [])]
  files.forEach(file => {
    const url  = URL.createObjectURL(file)
    const item = reactive({ id: ++assetIdSeq, name: file.name.replace(/\.[^.]+$/, ''), url, img: null })
    const img  = new Image()
    img.onload = () => { item.img = img }
    img.src    = url
    assetLibrary.value.push(item)
  })
  e.target.value = ''
}

// ── Layer management ───────────────────────────────────────────────────────
function addLayer(asset) {
  if (!asset.img) return
  layers.value.push({ id: ++layerIdSeq, name: asset.name, url: asset.url, img: asset.img, x: 0.5, y: 0.5, scale: 1.0 })
  selectedLayerIdx.value = layers.value.length - 1
  selectedTextIdx.value  = -1
}

function selectLayer(i) {
  selectedLayerIdx.value = i
  selectedTextIdx.value  = -1
}

function removeLayer(i) {
  layers.value.splice(i, 1)
  selectedLayerIdx.value = Math.min(selectedLayerIdx.value, layers.value.length - 1)
}

function moveLayerUp(i) {
  if (i >= layers.value.length - 1) return
  ;[layers.value[i], layers.value[i + 1]] = [layers.value[i + 1], layers.value[i]]
  selectedLayerIdx.value = i + 1
}

function moveLayerDown(i) {
  if (i <= 0) return
  ;[layers.value[i], layers.value[i - 1]] = [layers.value[i - 1], layers.value[i]]
  selectedLayerIdx.value = i - 1
}

function resetLayer(i) {
  layers.value[i].x     = 0.5
  layers.value[i].y     = 0.5
  layers.value[i].scale = 1.0
}

// ── Text management ────────────────────────────────────────────────────────
const today   = new Date()
const tanggal = today.toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })

texts.value.push(
  { id: ++textIdSeq, content: 'Ready Menus', x: 0.5, y: 0.08,
    fontSize: 80, color: '#ffffff', fontFamily: 'Impact', fontWeight: 'bold',
    italic: false, textAlign: 'center', shadow: true },
  { id: ++textIdSeq, content: tanggal, x: 0.5, y: 0.93,
    fontSize: 52, color: '#ffffff', fontFamily: 'Arial', fontWeight: 'normal',
    italic: false, textAlign: 'center', shadow: true }
)

function addText() {
  texts.value.push({
    id: ++textIdSeq, content: 'Teks Baru',
    x: 0.5, y: 0.5, fontSize: 72,
    color: '#ffffff', fontFamily: 'Arial', fontWeight: 'bold',
    italic: false, textAlign: 'center', shadow: true,
  })
  selectedTextIdx.value  = texts.value.length - 1
  selectedLayerIdx.value = -1
}

function removeText(i) {
  texts.value.splice(i, 1)
  if (selectedTextIdx.value >= texts.value.length)
    selectedTextIdx.value = texts.value.length - 1
}

// ── Draw helpers ───────────────────────────────────────────────────────────
function drawBgPhoto(ctx, img, cw, ch) {
  const baseS = Math.max(cw / img.width, ch / img.height) * bgPhotoScale.value
  const sw    = img.width  * baseS
  const sh    = img.height * baseS
  const ox    = Math.max(0, sw - cw)
  const oy    = Math.max(0, sh - ch)
  const dx    = (cw - sw) / 2 + (bgPhotoOffsetX.value - 0.5) * ox
  const dy    = (ch - sh) / 2 + (bgPhotoOffsetY.value - 0.5) * oy
  ctx.drawImage(img, dx, dy, sw, sh)
}

function getLayerRect(layer, cw, ch) {
  const baseS = Math.min(cw / layer.img.width, ch / layer.img.height)
  const lw    = layer.img.width  * baseS * layer.scale
  const lh    = layer.img.height * baseS * layer.scale
  const lx    = layer.x * cw - lw / 2
  const ly    = layer.y * ch - lh / 2
  return { lx, ly, lw, lh }
}

function buildFont(t, scale) {
  const style = t.italic ? 'italic' : 'normal'
  const size  = Math.max(1, Math.round(t.fontSize * scale))
  return `${style} ${t.fontWeight} ${size}px "${t.fontFamily}", Arial, sans-serif`
}

function drawCornerHandles(ctx, lx, ly, lw, lh) {
  const corners = [[lx, ly], [lx + lw, ly], [lx, ly + lh], [lx + lw, ly + lh]]
  corners.forEach(([cx, cy]) => {
    ctx.fillStyle = '#3b82f6'
    ctx.fillRect(cx - HANDLE_R, cy - HANDLE_R, HANDLE_R * 2, HANDLE_R * 2)
    ctx.strokeStyle = '#fff'
    ctx.lineWidth   = 1.5
    ctx.setLineDash([])
    ctx.strokeRect(cx - HANDLE_R + 1, cy - HANDLE_R + 1, (HANDLE_R - 1) * 2, (HANDLE_R - 1) * 2)
  })
}

// ── Core render ────────────────────────────────────────────────────────────
function drawAll(canvas) {
  if (!canvas) return
  const isExport = canvas !== previewCanvas.value
  const cw       = canvas.width
  const ch       = canvas.height
  const scale    = cw / CANVAS_W

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, cw, ch)

  if (bgType.value === 'color') {
    ctx.fillStyle = bgColor.value
    ctx.fillRect(0, 0, cw, ch)
  } else if (bgPhotoImg.value) {
    drawBgPhoto(ctx, bgPhotoImg.value, cw, ch)
  } else {
    ctx.fillStyle = '#e5e7eb'
    ctx.fillRect(0, 0, cw, ch)
    ctx.fillStyle = '#9ca3af'
    ctx.font      = `${14 * scale}px Arial`
    ctx.textAlign = 'center'
    ctx.fillText('Upload foto background', cw / 2, ch / 2)
  }

  layers.value.forEach((layer, i) => {
    if (!layer.img) return
    const { lx, ly, lw, lh } = getLayerRect(layer, cw, ch)
    ctx.drawImage(layer.img, lx, ly, lw, lh)
    if (!isExport && i === selectedLayerIdx.value) {
      ctx.save()
      ctx.setLineDash([5, 4])
      ctx.lineWidth   = 1.5
      ctx.strokeStyle = 'rgba(59,130,246,0.9)'
      ctx.strokeRect(lx, ly, lw, lh)
      drawCornerHandles(ctx, lx, ly, lw, lh)
      ctx.setLineDash([])
      ctx.fillStyle = 'rgba(59,130,246,0.25)'
      ctx.beginPath()
      ctx.arc(layer.x * cw, layer.y * ch, 10, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = '#3b82f6'
      ctx.lineWidth   = 1.5
      ctx.stroke()
      ctx.restore()
    }
  })

  texts.value.forEach((t, i) => {
    ctx.save()
    ctx.font = buildFont(t, scale)
    if (t.shadow) {
      ctx.shadowColor   = 'rgba(0,0,0,0.75)'
      ctx.shadowBlur    = 8 * scale
      ctx.shadowOffsetX = 2 * scale
      ctx.shadowOffsetY = 2 * scale
    }
    ctx.fillStyle    = t.color
    ctx.textAlign    = t.textAlign
    ctx.textBaseline = 'middle'
    const lines  = (t.content || '').split('\n')
    const lineH  = t.fontSize * scale * 1.35
    const totalH = lines.length * lineH
    lines.forEach((line, li) => {
      ctx.fillText(line, t.x * cw, t.y * ch - totalH / 2 + li * lineH + lineH / 2)
    })
    if (!isExport && i === selectedTextIdx.value && t.content) {
      ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0
      ctx.font = buildFont(t, scale)
      const longest = lines.reduce((a, b) => b.length > a.length ? b : a, '')
      const tw = ctx.measureText(longest).width
      let rx = t.textAlign === 'center' ? t.x * cw - tw / 2
             : t.textAlign === 'right'  ? t.x * cw - tw : t.x * cw
      ctx.setLineDash([4, 3])
      ctx.lineWidth = 1.5; ctx.strokeStyle = '#f59e0b'
      ctx.strokeRect(rx - 6, t.y * ch - totalH / 2 - 4, tw + 12, totalH + 8)
      ctx.setLineDash([])
      ctx.fillStyle = '#f59e0b'
      ctx.beginPath(); ctx.arc(t.x * cw, t.y * ch, 5, 0, Math.PI * 2); ctx.fill()
    }
    ctx.restore()
  })
}

function redraw() {
  if (!previewCanvas.value) return
  drawAll(previewCanvas.value)
}

watch(
  [bgType, bgColor, bgPhotoImg, bgPhotoScale, bgPhotoOffsetX, bgPhotoOffsetY,
   layers, selectedLayerIdx, texts, selectedTextIdx],
  () => nextTick(redraw),
  { deep: true }
)

// ── Background photo upload ────────────────────────────────────────────────
function onBgPhotoChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const img = new Image()
  img.onload = () => { bgPhotoImg.value = img }
  img.src    = URL.createObjectURL(file)
}

// ── Mouse / Touch helpers ──────────────────────────────────────────────────
function getCanvasPos(e) {
  const canvas = previewCanvas.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  return {
    x: (e.clientX - rect.left) * (DISPLAY_W / rect.width),
    y: (e.clientY - rect.top)  * (DISPLAY_H / rect.height),
  }
}

function getLayerBoxDisplay(layer) { return getLayerRect(layer, DISPLAY_W, DISPLAY_H) }

function isOnCorner(mx, my, lx, ly, lw, lh) {
  return [[lx, ly], [lx+lw, ly], [lx, ly+lh], [lx+lw, ly+lh]]
    .some(([cx, cy]) => Math.abs(mx-cx) <= HANDLE_R+3 && Math.abs(my-cy) <= HANDLE_R+3)
}

function isInRect(mx, my, lx, ly, lw, lh) {
  return mx >= lx && mx <= lx+lw && my >= ly && my <= ly+lh
}

function findLayerAt(mx, my) {
  for (let i = layers.value.length - 1; i >= 0; i--) {
    const l = layers.value[i]
    if (!l.img) continue
    const b = getLayerBoxDisplay(l)
    if (isInRect(mx, my, b.lx, b.ly, b.lw, b.lh)) return i
  }
  return -1
}

function findTextAt(mx, my) {
  for (let i = texts.value.length - 1; i >= 0; i--) {
    const t = texts.value[i]
    if (Math.hypot(mx - t.x * DISPLAY_W, my - t.y * DISPLAY_H) < 32) return i
  }
  return -1
}

// ── Mouse events ───────────────────────────────────────────────────────────
function onMouseDown(e) {
  const { x: mx, y: my } = getCanvasPos(e)
  if (selectedLayerIdx.value >= 0 && layers.value[selectedLayerIdx.value]?.img) {
    const b = getLayerBoxDisplay(layers.value[selectedLayerIdx.value])
    if (isOnCorner(mx, my, b.lx, b.ly, b.lw, b.lh)) {
      dragging.value         = true
      dragMode.value         = 'layer-resize'
      dragLayerIdx.value     = selectedLayerIdx.value
      resizeStartScale.value = layers.value[selectedLayerIdx.value].scale
      resizeStartDist.value  = Math.hypot(
        mx - layers.value[selectedLayerIdx.value].x * DISPLAY_W,
        my - layers.value[selectedLayerIdx.value].y * DISPLAY_H
      ) || 10
      return
    }
  }
  const li = findLayerAt(mx, my)
  if (li >= 0) {
    selectedLayerIdx.value = li; selectedTextIdx.value = -1
    dragging.value = true; dragMode.value = 'layer-move'; dragLayerIdx.value = li
    dragOffX.value = mx - layers.value[li].x * DISPLAY_W
    dragOffY.value = my - layers.value[li].y * DISPLAY_H
    return
  }
  const ti = findTextAt(mx, my)
  if (ti >= 0) {
    selectedTextIdx.value = ti; selectedLayerIdx.value = -1
    dragging.value = true; dragMode.value = 'text'; dragTextIdx.value = ti
    dragOffX.value = mx - texts.value[ti].x * DISPLAY_W
    dragOffY.value = my - texts.value[ti].y * DISPLAY_H
    return
  }
  selectedLayerIdx.value = -1; selectedTextIdx.value = -1
}

function onMouseMove(e) {
  const { x: mx, y: my } = getCanvasPos(e)
  if (!dragging.value) {
    if (selectedLayerIdx.value >= 0 && layers.value[selectedLayerIdx.value]?.img) {
      const b = getLayerBoxDisplay(layers.value[selectedLayerIdx.value])
      if (isOnCorner(mx, my, b.lx, b.ly, b.lw, b.lh)) { hoverMode.value = 'layer-resize'; return }
    }
    if (findLayerAt(mx, my) >= 0) { hoverMode.value = 'layer'; return }
    if (findTextAt(mx, my)  >= 0) { hoverMode.value = 'text';  return }
    hoverMode.value = null; return
  }
  if (dragMode.value === 'layer-move' && dragLayerIdx.value >= 0) {
    layers.value[dragLayerIdx.value].x = (mx - dragOffX.value) / DISPLAY_W
    layers.value[dragLayerIdx.value].y = (my - dragOffY.value) / DISPLAY_H
  } else if (dragMode.value === 'layer-resize' && dragLayerIdx.value >= 0) {
    const l    = layers.value[dragLayerIdx.value]
    const dist = Math.hypot(mx - l.x * DISPLAY_W, my - l.y * DISPLAY_H)
    l.scale    = Math.max(0.02, resizeStartScale.value * dist / resizeStartDist.value)
  } else if (dragMode.value === 'text' && dragTextIdx.value >= 0) {
    const t = texts.value[dragTextIdx.value]
    t.x = Math.max(0, Math.min(1, (mx - dragOffX.value) / DISPLAY_W))
    t.y = Math.max(0, Math.min(1, (my - dragOffY.value) / DISPLAY_H))
  }
}

function onMouseUp() {
  dragging.value = false; dragMode.value = null; dragLayerIdx.value = -1; dragTextIdx.value = -1
}

function onMouseLeave() { onMouseUp(); hoverMode.value = null }

function getTouch(e) {
  const t = e.touches[0] || e.changedTouches[0]
  return getCanvasPos(t)
}
function onTouchStart(e) { onMouseDown(getTouch(e)) }
function onTouchMove(e)  { if (dragging.value) onMouseMove(getTouch(e)) }
function onTouchEnd()    { onMouseUp() }

// ── Download ───────────────────────────────────────────────────────────────
async function downloadTwibon() {
  downloading.value = true
  await nextTick()
  try {
    const exportCanvas        = document.createElement('canvas')
    exportCanvas.width        = CANVAS_W
    exportCanvas.height       = CANVAS_H
    drawAll(exportCanvas)
    await nextTick()
    const a      = document.createElement('a')
    a.download   = `twibon_${Date.now()}.png`
    a.href       = exportCanvas.toDataURL('image/png')
    a.click()
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped>
.slide-fade-enter-active, .slide-fade-leave-active { transition: all .2s ease; }
.slide-fade-enter-from, .slide-fade-leave-to { opacity: 0; transform: translateY(-6px); }
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
