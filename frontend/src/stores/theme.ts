import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface ThemeOption {
  id: string;
  name: string;
  type: 'dark' | 'light';
  colors: string[]; // [primary, secondary, accent, base]
}

export const DAISY_THEMES: ThemeOption[] = [
  // Popular Dark Themes
  { id: 'night', name: '夜幕 (Night)', type: 'dark', colors: ['#38bdf8', '#818cf8', '#f472b6', '#0f172a'] },
  { id: 'dim', name: '暗曜 (Dim)', type: 'dark', colors: ['#9fe88d', '#ff7b72', '#79c0ff', '#22272e'] },
  { id: 'dark', name: '深邃黑 (Dark)', type: 'dark', colors: ['#6419e6', '#d926a9', '#1fb2a6', '#191d24'] },
  { id: 'sunset', name: '落日熔金 (Sunset)', type: 'dark', colors: ['#ff865b', '#fd6f9c', '#b387fa', '#121c24'] },
  { id: 'dracula', name: '吸血鬼 (Dracula)', type: 'dark', colors: ['#ff79c6', '#bd93f9', '#ffb86c', '#282a36'] },
  { id: 'synthwave', name: '合成波 (Synthwave)', type: 'dark', colors: ['#e779c1', '#58c7f3', '#f3cc30', '#1a103c'] },
  { id: 'luxury', name: '黑金奢华 (Luxury)', type: 'dark', colors: ['#ffffff', '#152747', '#513448', '#09090b'] },
  { id: 'forest', name: '暗影森 (Forest)', type: 'dark', colors: ['#1eb854', '#1db990', '#1db9ac', '#171212'] },
  { id: 'black', name: '极夜纯黑 (Black)', type: 'dark', colors: ['#343232', '#343232', '#343232', '#000000'] },
  { id: 'coffee', name: '香醇咖啡 (Coffee)', type: 'dark', colors: ['#db924b', '#263e3f', '#10576d', '#20161f'] },
  { id: 'business', name: '商务精英 (Business)', type: 'dark', colors: ['#1c4e80', '#7ea8be', '#ea6947', '#202020'] },
  { id: 'halloween', name: '万圣之夜 (Halloween)', type: 'dark', colors: ['#f28c18', '#6d3baf', '#51a800', '#212121'] },
  
  // Popular Light & Bright Themes
  { id: 'nord', name: '北欧极简 (Nord)', type: 'light', colors: ['#5e81ac', '#81a1c1', '#88c0d0', '#eceff4'] },
  { id: 'winter', name: '冬日雪境 (Winter)', type: 'light', colors: ['#047aff', '#463aa2', '#c148ac', '#ffffff'] },
  { id: 'light', name: '明亮白 (Light)', type: 'light', colors: ['#570df8', '#f000b8', '#37cdbe', '#ffffff'] },
  { id: 'cupcake', name: '甜心纸杯 (Cupcake)', type: 'light', colors: ['#65c3c8', '#ef9fbc', '#eeaf3a', '#faf7f5'] },
  { id: 'corporate', name: '现代商务 (Corporate)', type: 'light', colors: ['#4b6bfb', '#7b92b2', '#67cba0', '#ffffff'] },
  { id: 'emerald', name: '翡翠青绿 (Emerald)', type: 'light', colors: ['#66cc8a', '#377cfb', '#ea5234', '#ffffff'] },
  { id: 'retro', name: '复古唱片 (Retro)', type: 'light', colors: ['#ef9995', '#a4cbb4', '#ebdc99', '#ece3ca'] },
  { id: 'cyberpunk', name: '赛博朋克 (Cyberpunk)', type: 'light', colors: ['#ff7598', '#ff7598', '#2dd4bf', '#ffee00'] },
  { id: 'valentine', name: '粉红告白 (Valentine)', type: 'light', colors: ['#e96d7b', '#a991f7', '#88dbdd', '#f0d6e8'] },
  { id: 'garden', name: '幽静花木 (Garden)', type: 'light', colors: ['#5c7f67', '#ecf0ea', '#c68a4c', '#e9e7e7'] },
  { id: 'aqua', name: '水色碧蓝 (Aqua)', type: 'dark', colors: ['#09ecf3', '#966fb3', '#ffe999', '#3b5998'] },
  { id: 'lofi', name: '极简素雅 (Lo-fi)', type: 'light', colors: ['#0d0d0d', '#1a1919', '#262626', '#ffffff'] },
  { id: 'pastel', name: '马卡龙柔色 (Pastel)', type: 'light', colors: ['#d1c1d7', '#f6cbd1', '#b4e9d6', '#ffffff'] },
  { id: 'fantasy', name: '奇幻魔法 (Fantasy)', type: 'light', colors: ['#6e0b75', '#007ebd', '#f8860d', '#ffffff'] },
  { id: 'wireframe', name: '线框简绘 (Wireframe)', type: 'light', colors: ['#b8b8b8', '#b8b8b8', '#b8b8b8', '#ffffff'] },
  { id: 'cmyk', name: '印刷四色 (CMYK)', type: 'light', colors: ['#45aeee', '#e8488a', '#fff232', '#ffffff'] },
  { id: 'autumn', name: '秋意枫红 (Autumn)', type: 'light', colors: ['#8c0327', '#d85251', '#d59b6a', '#f1f1f1'] },
  { id: 'acid', name: '酸性霓虹 (Acid)', type: 'light', colors: ['#ff00f4', '#ff7a00', '#99feff', '#fafafa'] },
  { id: 'lemonade', name: '清新柠檬 (Lemonade)', type: 'light', colors: ['#519903', '#e9e92f', '#dff333', '#fcfcfc'] },
  { id: 'bumblebee', name: '黄蜂活力 (Bumblebee)', type: 'light', colors: ['#e0a82e', '#f9d72f', '#181830', '#ffffff'] }
];

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref<string>(localStorage.getItem('unitdeck_theme') || 'night');

  function setTheme(theme: string) {
    currentTheme.value = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('unitdeck_theme', theme);
  }

  // Initialize on load
  setTheme(currentTheme.value);

  return { currentTheme, themes: DAISY_THEMES, setTheme };
});
