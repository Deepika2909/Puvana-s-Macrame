// document.querySelectorAll('.increase').forEach(button => {
//     button.addEventListener('click', () => {
//         const input = button.previousElementSibling;
//         input.value = parseInt(input.value) + 1;
//         updateCart();
//     });
// });

// document.querySelectorAll('.decrease').forEach(button => {
//     button.addEventListener('click', () => {
//         const input = button.nextElementSibling;
//         if (input.value > 1) {
//             input.value = parseInt(input.value) - 1;
//             updateCart();
//         }
//     });
// });

// document.querySelectorAll('.remove-item').forEach(button => {
//     button.addEventListener('click', () => {
//         button.closest('.cart-item').remove();
//         updateCart();
//     });
// });

// function updateCart() {
//     // Update cart total and other details
// }

// cart.js
const cartItemsContainer = document.querySelector('.cart-items');
const cartSummary = document.querySelector('.cart-summary');
const cartTotalElement = document.getElementById('cartTotal');
const ptop = document.getElementById('ptop');

// Function to update the cart total
function updateCartTotal() {
    let cartTotal = 0;
    const cartItems = cartItemsContainer.querySelectorAll('.cart-item');
    cartItems.forEach(item => {
        const priceElement = item.querySelector('.item-details .p4:first-of-type');
        const quantityElement = item.querySelector('.quantity-control input');
        const price = parseFloat(priceElement.textContent.replace(/[₹\s]/g, '').trim());
        const quantity = parseInt(quantityElement.value);
        cartTotal += price * quantity;
    });
    cartTotalElement.textContent = `₹${cartTotal.toFixed(2)}`;
    ptop.textContent = `Subtotal: ₹${cartTotal.toFixed(2)}`;
}

// Function to add an item to the cart
function addToCart(item) {
    // Get the product details
    const imageSrc = item.querySelector('.product-image').src;
    const title = item.querySelector('#des h5').textContent;
    const price = parseFloat(item.querySelector('#des p1').textContent.replace(/[₹\s]/g, '').trim());

    // Create a new cart item element
    const cartItem = document.createElement('div');
    cartItem.classList.add('cart-item');
    cartItem.innerHTML = `
        <img src="${imageSrc}" alt="${title}" class="cartitemimg">
        <div class="item-details">
            <h1>${title}</h1>
            <p class="p4">₹ ${price.toFixed(2)}</p>
            <div class="quantity-control">
                <button class="decrease">-</button>
                <input type="number" value="1" min="1">
                <button class="increase">+</button>
            </div>
            <button class="remove-item">Remove</button>
        </div>
    `;

    // Add the new cart item to the cart container
    cartItemsContainer.appendChild(cartItem);

    // Add event listeners to quantity control buttons
    const quantityInput = cartItem.querySelector('.quantity-control input');
    const decreaseButton = cartItem.querySelector('.decrease');
    const increaseButton = cartItem.querySelector('.increase');

    decreaseButton.addEventListener('click', () => {
        let qty = parseInt(quantityInput.value);
        if (qty > 1) {
            quantityInput.value = qty - 1;
            updateCartTotal();
        }
    });

    increaseButton.addEventListener('click', () => {
        let qty = parseInt(quantityInput.value);
        quantityInput.value = qty + 1;
        updateCartTotal();
    });

    // Add event listener to remove item button
    const removeButton = cartItem.querySelector('.remove-item');
    removeButton.addEventListener('click', () => {
        cartItem.remove();
        updateCartTotal();
    });

    console.log('addToCart called with item:', item);

    // Update the cart total
    updateCartTotal();
}

// Add event listeners to "Add to Cart" buttons in the shop page
const addToCartButtons = document.querySelectorAll('#addToCartBtn');
addToCartButtons.forEach(button => {
    button.addEventListener('click', () => {
        addToCart(button.closest('.product-item'));
    });
});

// ✅ Add event listeners to already rendered cart items (from backend/template)
document.addEventListener('DOMContentLoaded', () => {
    const cartItems = document.querySelectorAll('.cart-item');

    function updateCartTotal() {
        let subtotal = 0;
        cartItems.forEach(item => {
            const priceText = item.querySelector('.p4').textContent.replace(/[₹\s]/g, '');
            const quantity = parseInt(item.querySelector('input[type="number"]').value);
            subtotal += parseFloat(priceText) * quantity;
        });
        const total = subtotal + 50;
        document.getElementById('ptop').textContent = `Subtotal: ₹${subtotal.toFixed(2)}`;
        document.getElementById('cartTotal').textContent = `Total: ₹${total.toFixed(2)}`;
    }

    cartItems.forEach(item => {
        const increaseBtn = item.querySelector('.increase');
        const decreaseBtn = item.querySelector('.decrease');
        const input = item.querySelector('input[type="number"]');

        increaseBtn.addEventListener('click', () => {
            input.value = parseInt(input.value) + 1;
            updateCartTotal();
        });

        decreaseBtn.addEventListener('click', () => {
            if (parseInt(input.value) > 1) {
                input.value = parseInt(input.value) - 1;
                updateCartTotal();
            }
        });

        input.addEventListener('change', () => {
            if (parseInt(input.value) < 1) input.value = 1;
            updateCartTotal();
        });
    });

    updateCartTotal();
});
