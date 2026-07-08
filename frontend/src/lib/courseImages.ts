// Unsplash hero images keyed by exact category name (as seeded in the DB).
// Wide format (w=800) for detail page banners; card thumbnails use w=400.

const CATEGORY_PHOTOS: Record<string, string> = {
  'Power Systems & High Voltage':
    'photo-1621905251918-48416bd8575a',
  'Electrical Installation':
    'photo-1558618666-fcd25c85cd64',
  'Mechanical & Industrial Engineering':
    'photo-1581092160562-40aa08e78837',
  'Civil & Construction Engineering':
    'photo-1504307651254-35680f356dfd',
  'Renewable Energy & Sustainability':
    'photo-1509391366360-2e959784a276',
  'Management, Finance & Leadership':
    'photo-1556761175-5973dc0f32e7',
  'Health, Safety & HR Compliance':
    'photo-1584634731339-252c581abfc5',
}

const FALLBACK_PHOTO = 'photo-1517245386807-bb43f82c33c4'

function unsplashUrl(photoId: string, width: number, height: number) {
  return `https://images.unsplash.com/${photoId}?auto=format&fit=crop&w=${width}&h=${height}&q=75`
}

export function getCourseCardImage(categoryName?: string | null): string {
  const id = (categoryName && CATEGORY_PHOTOS[categoryName]) || FALLBACK_PHOTO
  return unsplashUrl(id, 400, 200)
}

export function getCourseHeroImage(categoryName?: string | null): string {
  const id = (categoryName && CATEGORY_PHOTOS[categoryName]) || FALLBACK_PHOTO
  return unsplashUrl(id, 900, 340)
}

// For CategoryChips (keeps the same photo IDs, different size)
export function getCategoryChipImage(categoryName: string): string {
  const id = CATEGORY_PHOTOS[categoryName] || FALLBACK_PHOTO
  return unsplashUrl(id, 400, 200)
}
