<template>
  <div class="px-3 pt-4 pb-1">
    <p class="text-xs font-bold text-gray-300 uppercase tracking-widest">{{ label }}</p>
  </div>
</template>

<script setup>
defineProps({ label: String })
</script>
