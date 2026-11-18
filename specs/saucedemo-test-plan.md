# SauceDemo UI Functional Test Plan

## Application Overview

Comprehensive, independently executable UI functional test plan for SauceDemo at https://www.saucedemo.com/, based on live Playwright browser exploration. Observed application title: Swag Labs. Each case must run in a fresh browser context with local/session storage cleared, begin at the login URL, and perform its own authentication/setup. Use the documented standard_user / secret_sauce unless a negative or locked-out test specifies otherwise. Assert observable behavior through accessible roles/names, data-test selectors, stable visible text, and URL; rely on Playwright auto-waiting and state-based assertions, never fixed sleeps. Product catalog observed in default A-Z order: Sauce Labs Backpack ($29.99), Sauce Labs Bike Light ($9.99), Sauce Labs Bolt T-Shirt ($15.99), Sauce Labs Fleece Jacket ($49.99), Sauce Labs Onesie ($7.99), Test.allTheThings() T-Shirt (Red) ($15.99). Sort options observed: az, za, lohi, hilo. Cart rows show quantity 1 per distinct product, with add/remove toggles; cart exposes no quantity editor. Checkout has required First Name, Last Name, Zip/Postal Code fields. Observed totals for backpack: item total $29.99, tax $2.40, total $32.39; payment SauceCard #31337; shipping Free Pony Express Delivery!. Observed zero-item boundary: checkout is allowed, overview totals are $0 / $0.00 / $0.00, and Finish reaches the normal order confirmation. Logout returns to login and direct /inventory.html access while logged out redirects to login with a login-required alert. No Playwright automation scenarios are authored by this plan; the file paths below are proposed future automation targets only. Each scenario includes its unique ID, preconditions, test data, steps, and expected results. Independent runs should reset browser context/local storage before each case to avoid state carried across logout/login.

## Test Scenarios

### 1. Login functionality

**Seed:** `tests/seed.spec.ts`

#### 1.1. LOGIN_TC_001 - Standard user logs in successfully

**File:** `tests/saucedemo/login.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context, logged out, at https://www.saucedemo.com/. Test data: username=standard_user; password=secret_sauce.
    - expect: Login form is visible with Username, Password, and Login controls.
  2. Fill Username and Password with the specified values, then activate Login.
    - expect: URL becomes https://www.saucedemo.com/inventory.html.
    - expect: Products heading and six catalog items are visible.

#### 1.2. LOGIN_TC_002 - Empty username and password are rejected

**File:** `tests/saucedemo/login.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context at the login page. Test data: username empty; password empty.
    - expect: Login form is visible.
  2. Activate Login without entering either value.
    - expect: Remain on the login page.
    - expect: Alert reads: Epic sadface: Username is required.

#### 1.3. LOGIN_TC_003 - Missing password is rejected

**File:** `tests/saucedemo/login.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context at the login page. Test data: username=standard_user; password empty.
    - expect: Login form is visible.
  2. Fill Username only and activate Login.
    - expect: Remain on the login page.
    - expect: Alert reads: Epic sadface: Password is required.

#### 1.4. LOGIN_TC_004 - Invalid credentials are rejected

**File:** `tests/saucedemo/login.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context at the login page. Test data: username=standard_user; password=wrong_password.
    - expect: Login form is visible.
  2. Enter the specified username and invalid password, then activate Login.
    - expect: Remain on the login page.
    - expect: Alert reads: Epic sadface: Username and password do not match any user in this service.

#### 1.5. LOGIN_TC_005 - Locked-out user cannot log in

**File:** `tests/saucedemo/login.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context at the login page. Test data: username=locked_out_user; password=secret_sauce.
    - expect: Login form is visible.
  2. Enter the documented locked-out username and password, then activate Login.
    - expect: Remain on the login page.
    - expect: Alert reads: Epic sadface: Sorry, this user has been locked out.

### 2. Product listing, details, and sorting

**Seed:** `tests/seed.spec.ts`

#### 2.1. PRODUCT_TC_001 - Default product listing shows all six products

**File:** `tests/saucedemo/products.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce and open the inventory page. Test data: expected catalog is the six observed SauceDemo products and prices.
    - expect: Products heading is visible.
    - expect: Exactly six product cards are visible in default A-to-Z order: Sauce Labs Backpack $29.99; Sauce Labs Bike Light $9.99; Sauce Labs Bolt T-Shirt $15.99; Sauce Labs Fleece Jacket $49.99; Sauce Labs Onesie $7.99; Test.allTheThings() T-Shirt (Red) $15.99.
    - expect: Each product card exposes an Add to cart action.

#### 2.2. PRODUCT_TC_002 - Product detail shows backpack information and returns to catalog

**File:** `tests/saucedemo/products.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce and open the inventory page. Test data: Sauce Labs Backpack.
    - expect: Backpack product card is visible.
  2. Open the Sauce Labs Backpack product details using its product image or name.
    - expect: URL is https://www.saucedemo.com/inventory-item.html?id=4.
    - expect: Details show Sauce Labs Backpack, its product image, description 'carry.allTheThings() with the sleek, streamlined Sly Pack that melds uncompromising style with unequaled laptop and tablet protection.', price $29.99, and Add to cart.
  3. Activate Back to products.
    - expect: URL returns to /inventory.html and the product listing is visible.

#### 2.3. PRODUCT_TC_003 - Adding a product from details updates its action and cart badge

**File:** `tests/saucedemo/products.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in as standard_user / secret_sauce. Test data: Sauce Labs Backpack.
    - expect: Backpack detail page opens with Add to cart visible.
  2. Activate Add to cart on the backpack detail page.
    - expect: The action changes to Remove.
    - expect: Cart badge displays 1 item.

#### 2.4. SORT_TC_001 - Products default to name ascending

**File:** `tests/saucedemo/sorting.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce. Test data: sort value az.
    - expect: Sort products control is visible with Name (A to Z) selected.
  2. Read visible product names in their displayed order.
    - expect: Names appear in ascending order: Sauce Labs Backpack; Sauce Labs Bike Light; Sauce Labs Bolt T-Shirt; Sauce Labs Fleece Jacket; Sauce Labs Onesie; Test.allTheThings() T-Shirt (Red).

#### 2.5. SORT_TC_002 - Name descending sort orders products Z to A

**File:** `tests/saucedemo/sorting.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce. Test data: select sort value za.
    - expect: Sort products control is visible.
  2. Select Name (Z to A) and read the visible product names in order.
    - expect: Names appear in descending order: Test.allTheThings() T-Shirt (Red); Sauce Labs Onesie; Sauce Labs Fleece Jacket; Sauce Labs Bolt T-Shirt; Sauce Labs Bike Light; Sauce Labs Backpack.

#### 2.6. SORT_TC_003 - Price ascending sort orders products low to high

**File:** `tests/saucedemo/sorting.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce. Test data: select sort value lohi.
    - expect: Sort products control is visible.
  2. Select Price (low to high) and read visible product names and prices.
    - expect: Prices are non-decreasing and displayed as: Sauce Labs Onesie $7.99; Sauce Labs Bike Light $9.99; Sauce Labs Bolt T-Shirt $15.99; Test.allTheThings() T-Shirt (Red) $15.99; Sauce Labs Backpack $29.99; Sauce Labs Fleece Jacket $49.99.

#### 2.7. SORT_TC_004 - Price descending sort orders products high to low

**File:** `tests/saucedemo/sorting.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce. Test data: select sort value hilo.
    - expect: Sort products control is visible.
  2. Select Price (high to low) and read visible product names and prices.
    - expect: Prices are non-increasing and displayed as: Sauce Labs Fleece Jacket $49.99; Sauce Labs Backpack $29.99; Sauce Labs Bolt T-Shirt $15.99; Test.allTheThings() T-Shirt (Red) $15.99; Sauce Labs Bike Light $9.99; Sauce Labs Onesie $7.99.

### 3. Shopping cart

**Seed:** `tests/seed.spec.ts`

#### 3.1. CART_TC_001 - Add one product and verify its cart contents

**File:** `tests/saucedemo/cart.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in as standard_user / secret_sauce. Test data: Sauce Labs Backpack ($29.99).
    - expect: Inventory page shows the backpack with Add to cart.
  2. Activate Add to cart, then open the cart.
    - expect: Cart badge displays 1.
    - expect: Cart contains exactly Sauce Labs Backpack at $29.99 with quantity 1 and a Remove action.

#### 3.2. CART_TC_002 - Multiple distinct products appear as separate cart rows

**File:** `tests/saucedemo/cart.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in as standard_user / secret_sauce. Test data: Sauce Labs Backpack ($29.99) and Sauce Labs Bike Light ($9.99).
    - expect: Inventory page is visible with both products.
  2. Add both products and open the cart.
    - expect: Cart badge displays 2.
    - expect: Cart has exactly two rows: backpack ($29.99, quantity 1) and bike light ($9.99, quantity 1).

#### 3.3. CART_TC_003 - Removing one cart item preserves the other

**File:** `tests/saucedemo/cart.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in and add backpack and bike light. Test data: remove Sauce Labs Bike Light.
    - expect: Cart shows both expected rows and badge 2.
  2. Activate Remove for Sauce Labs Bike Light.
    - expect: Bike Light row is absent; Backpack remains at quantity 1.
    - expect: Cart badge displays 1.

#### 3.4. CART_TC_004 - Removing the final item leaves an empty cart

**File:** `tests/saucedemo/cart.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in and add Sauce Labs Backpack. Test data: one backpack item.
    - expect: Cart contains one backpack row and badge 1.
  2. Activate Remove for the backpack in the cart.
    - expect: No cart rows remain and no cart badge is displayed.
    - expect: Continue Shopping and Checkout controls remain visible.

#### 3.5. CART_TC_005 - Remove from product listing clears cart state

**File:** `tests/saucedemo/cart.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in as standard_user / secret_sauce. Test data: Sauce Labs Backpack.
    - expect: Backpack card exposes Add to cart.
  2. Add the backpack, then activate its listing-level Remove action.
    - expect: Cart badge is absent.
    - expect: Backpack action returns to Add to cart.

#### 3.6. CART_TC_006 - A selected product has quantity one and cannot be duplicated by the add toggle

**File:** `tests/saucedemo/cart.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in as standard_user / secret_sauce. Test data: Sauce Labs Backpack.
    - expect: Backpack card initially exposes Add to cart.
  2. Add the backpack and inspect its card and cart row without removing it.
    - expect: Listing action toggles to Remove rather than another Add to cart control.
    - expect: Cart contains one backpack row with quantity 1; badge displays 1.
    - expect: Cart UI has no quantity editor or increment/decrement control.

### 4. Checkout and order completion

**Seed:** `tests/seed.spec.ts`

#### 4.1. CHECKOUT_TC_001 - Empty checkout form requires first name

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in and add Sauce Labs Backpack, open cart, then Checkout. Test data: all checkout information fields empty.
    - expect: Checkout: Your Information form shows First Name, Last Name, Zip/Postal Code, Cancel, and Continue.
  2. Activate Continue with all fields blank.
    - expect: Stay on checkout information page.
    - expect: Alert reads: Error: First Name is required.

#### 4.2. CHECKOUT_TC_002 - Checkout requires last name

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in and add backpack, then open checkout information. Test data: First Name=Avery; Last Name empty; Zip/Postal Code empty.
    - expect: Checkout information form is visible.
  2. Fill only First Name with Avery and activate Continue.
    - expect: Stay on checkout information page.
    - expect: Alert reads: Error: Last Name is required.

#### 4.3. CHECKOUT_TC_003 - Checkout requires postal code

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in and add backpack, then open checkout information. Test data: First Name=Avery; Last Name=Tester; Zip/Postal Code empty.
    - expect: Checkout information form is visible.
  2. Fill First Name and Last Name, leave Zip/Postal Code blank, and activate Continue.
    - expect: Stay on checkout information page.
    - expect: Alert reads: Error: Postal Code is required.

#### 4.4. CHECKOUT_TC_004 - Valid checkout information produces the expected overview totals

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in and add Sauce Labs Backpack. Test data: First Name=Avery; Last Name=Tester; Zip/Postal Code=10001.
    - expect: Cart contains backpack and Checkout is available.
  2. Open checkout, fill all three required fields, and activate Continue.
    - expect: URL becomes /checkout-step-two.html.
    - expect: Overview contains backpack, SauceCard #31337 payment information, and Free Pony Express Delivery! shipping information.
    - expect: Item total is $29.99, tax is $2.40, and total is $32.39.
    - expect: Cancel and Finish controls are visible.

#### 4.5. CHECKOUT_TC_005 - Canceling checkout information returns to cart and preserves items

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in and add backpack, open cart, and select Checkout. Test data: one backpack.
    - expect: Checkout: Your Information form is visible.
  2. Activate Cancel.
    - expect: URL returns to /cart.html.
    - expect: Backpack row remains at quantity 1 and cart badge remains 1.

#### 4.6. CHECKOUT_TC_006 - Finishing checkout confirms the order and clears the cart

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context with empty cart; sign in and add backpack. Test data: First Name=Avery; Last Name=Tester; Zip/Postal Code=10001.
    - expect: Inventory page and backpack item are available.
  2. Open cart, checkout, enter the test data, continue to overview, and select Finish.
    - expect: URL becomes /checkout-complete.html.
    - expect: Heading reads Thank you for your order! and dispatch confirmation text is visible.
    - expect: Cart badge indicates an empty cart.
    - expect: Back Home control is visible.

#### 4.7. CHECKOUT_TC_007 - Empty-cart checkout shows zero totals and completes

**File:** `tests/saucedemo/checkout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in but do not add any products. Test data: First Name=Zero; Last Name=Items; Zip/Postal Code=00000.
    - expect: Cart is empty and Checkout is available.
  2. Select Checkout, enter all required information, and Continue.
    - expect: Checkout overview contains no product rows.
    - expect: Item total is $0, tax is $0.00, and total is $0.00.
    - expect: Finish is available.
  3. Select Finish.
    - expect: URL becomes /checkout-complete.html and Thank you for your order! is shown.
    - expect: This is a boundary behavior observed in the application; the test records current behavior rather than asserting a different business policy.

### 5. Logout

**Seed:** `tests/seed.spec.ts`

#### 5.1. LOGOUT_TC_001 - Logout returns the user to the login page

**File:** `tests/saucedemo/logout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce and open the navigation menu. Test data: standard user session.
    - expect: Logout menu item is visible.
  2. Select Logout.
    - expect: URL returns to https://www.saucedemo.com/.
    - expect: Login form shows Username, Password, and Login controls.

#### 5.2. LOGOUT_TC_002 - Logged-out user cannot open inventory directly

**File:** `tests/saucedemo/logout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context; sign in as standard_user / secret_sauce, log out, then navigate directly to https://www.saucedemo.com/inventory.html. Test data: logged-out session.
    - expect: Application redirects to the root login URL.
  2. Inspect the login page alert.
    - expect: Alert indicates: You can only access '/inventory.html' when you are logged in.

#### 5.3. LOGOUT_TC_003 - Cart contents persist after logout and re-login in the same context

**File:** `tests/saucedemo/logout.spec.ts`

**Steps:**
  1. Preconditions: fresh isolated browser context and empty cart; sign in as standard_user / secret_sauce. Test data: add Sauce Labs Backpack, then log out and re-authenticate as standard_user / secret_sauce in the same browser context.
    - expect: Backpack is added and cart badge displays 1 before logout.
  2. After logging in again, inspect inventory and cart badge.
    - expect: Inventory page is visible after re-login.
    - expect: Backpack remains marked Remove and cart badge displays 1, matching the observed same-context persistence behavior.
