// 查看Element Plus中与发送消息相关的图标
import * as Icons from '@element-plus/icons-vue';

// 查找与发送、消息相关的图标
const sendRelatedIcons = Object.keys(Icons).filter(iconName => 
  iconName.toLowerCase().includes('send') || 
  iconName.toLowerCase().includes('message') ||
  iconName.toLowerCase().includes('chat')
);

console.log('Element Plus 与发送消息相关的图标:');
console.log(sendRelatedIcons);