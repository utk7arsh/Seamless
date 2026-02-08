/**
 * Content-scoped product data. Each content item (show/episode) can have associated
 * products in ready-to-buy format: product name, link, price, description.
 */
export interface ProductItem {
  product: string;
  link: string;
  price: number;
  description: string;
  source?: string;
}

export interface ContentProductsEntry {
  /** User id (matches AppUser.id from content.ts). */
  userId: number;
  contentId: string;
  products: ProductItem[];
}

import productsJson from "./contentProducts.json";

const entries = productsJson as ContentProductsEntry[];
const productsByUserAndContent = new Map<string, ProductItem[]>(
  entries.map((e) => [`${e.userId}-${e.contentId}`, e.products])
);

/**
 * Returns products for the given content and user. Different users get different products
 * for the same content (user-based product targeting). Returns an empty array if none are defined.
 */
export function getProductsForContent(contentId: string, userId: number): ProductItem[] {
  const key = `${userId}-${contentId}`;
  return productsByUserAndContent.get(key) ?? [];
}
