// Generate consistent color for each source
export const getSourceColor = (source) => {
  if (!source) source = 'default';
  const colors = [
    { bg: 'bg-blue-100', border: 'border-blue-600', text: 'text-blue-800', hover: 'hover:bg-blue-200' },
    { bg: 'bg-green-100', border: 'border-green-600', text: 'text-green-800', hover: 'hover:bg-green-200' },
    { bg: 'bg-purple-100', border: 'border-purple-600', text: 'text-purple-800', hover: 'hover:bg-purple-200' },
    { bg: 'bg-orange-100', border: 'border-orange-600', text: 'text-orange-800', hover: 'hover:bg-orange-200' },
    { bg: 'bg-pink-100', border: 'border-pink-600', text: 'text-pink-800', hover: 'hover:bg-pink-200' },
    { bg: 'bg-indigo-100', border: 'border-indigo-600', text: 'text-indigo-800', hover: 'hover:bg-indigo-200' },
    { bg: 'bg-red-100', border: 'border-red-600', text: 'text-red-800', hover: 'hover:bg-red-200' },
    { bg: 'bg-teal-100', border: 'border-teal-600', text: 'text-teal-800', hover: 'hover:bg-teal-200' },
  ];

  let hash = 0;
  for (let i = 0; i < source.length; i++) {
    hash = ((hash << 5) - hash) + source.charCodeAt(i);
    hash = hash & hash;
  }
  return colors[Math.abs(hash) % colors.length];
};
