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
  contentId: string;
  products: ProductItem[];
}

import productsJson from "./contentProducts.json";

const entries = productsJson as ContentProductsEntry[];
const productsByContent = new Map<string, ProductItem[]>(
  entries.map((e) => [e.contentId, e.products])
);

/**
 * Returns products for the given content (e.g. pizza for Breaking Bad, Pepsi for Stranger Things).
 * Returns an empty array if none are defined.
 */
export function getProductsForContent(contentId: string): ProductItem[] {
  return productsByContent.get(contentId) ?? [];
}
