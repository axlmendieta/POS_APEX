export const products = [
    { barcode: "123", name: "Milk 1L", price: 25.50, weighted: false, category: "Dairy" },
    { barcode: "456", name: "Bread", price: 45.00, weighted: false, category: "Bakery" },
    { barcode: "789", name: "Bananas", price: 18.00, weighted: true, category: "Produce" }, // Price per kg
    { barcode: "321", name: "Soda 600ml", price: 15.00, weighted: false, category: "Beverages" },
    { barcode: "654", name: "Avocado", price: 85.00, weighted: true, category: "Produce" },
    { barcode: "987", name: "Tortillas 1kg", price: 22.00, weighted: false, category: "Bakery" },
    { barcode: "111", name: "Eggs (12pk)", price: 38.00, weighted: false, category: "Dairy" },
    { barcode: "222", name: "Ice Bag 5kg", price: 30.00, weighted: false, category: "General" },
];

export const quickItems = [
    { name: "Bread", image: "🍞", barcode: "456" },
    { name: "Ice", image: "🧊", barcode: "222" },
    { name: "Avocado", image: "🥑", barcode: "654" },
    { name: "Tortillas", image: "🌮", barcode: "987" },
    { name: "Milk", image: "🥛", barcode: "123" },
    { name: "Soda", image: "🥤", barcode: "321" },
];
