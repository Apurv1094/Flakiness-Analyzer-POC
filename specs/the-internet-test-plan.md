# The Internet UI Functional Test Plan

## Application Overview

A browser-explored plan of exactly 30 independent, repeatable Playwright scenarios for The Internet demo application. The scenarios cover Dynamic Loading, Dynamic Controls, Disappearing Elements, Challenging DOM, Form Authentication, Dynamic Content, Add/Remove Elements, JavaScript Alerts, Status Codes, and Multiple Windows. Each test should use a fresh browser context; dynamic outcomes should be asserted through web-first synchronization rather than fixed delays. Categories are diagnostic possibilities, not predictions.

## Test Scenarios

### 1. Dynamic Loading

**Seed:** `No seed file; browser exploration only.`

#### 1.1. TC_001 - Existing hidden element becomes visible

**File:** `tests/the-internet/dynamic-loading.spec.ts`

**Steps:**
  1. Open /dynamic_loading/1, confirm the hidden result is not visible, and activate Start.
    - expect: The loading state is handled without fixed sleeps.
    - expect: The result becomes visible and reads Hello World!

#### 1.2. TC_002 - Dynamically inserted result appears after Start

**File:** `tests/the-internet/dynamic-loading.spec.ts`

**Steps:**
  1. Open /dynamic_loading/2, verify the result is not initially rendered, and activate Start.
    - expect: The dynamically inserted result eventually appears.
    - expect: The result reads Hello World!

#### 1.3. TC_003 - Loading indicator transitions to the final result

**File:** `tests/the-internet/dynamic-loading.spec.ts`

**Steps:**
  1. On a fresh /dynamic_loading/2 page, activate Start and synchronize on the loading indicator followed by the final result.
    - expect: Loading... is shown during the asynchronous transition when observable.
    - expect: The final Hello World! result is visible and the loading indicator is gone.

### 2. Dynamic Controls

**Seed:** `No seed file; browser exploration only.`

#### 2.1. TC_004 - Remove and restore the checkbox

**File:** `tests/the-internet/dynamic-controls.spec.ts`

**Steps:**
  1. Open /dynamic_controls, activate Remove, then wait for the removal completion and activate Add.
    - expect: The checkbox is removed and the confirmation reads It's gone!
    - expect: After Add completes, the checkbox is present again and the confirmation reads It's back!

#### 2.2. TC_005 - Enable input and enter text

**File:** `tests/the-internet/dynamic-controls.spec.ts`

**Steps:**
  1. Open /dynamic_controls, verify the text field is disabled, activate Enable, wait for the completion, and type a sample value.
    - expect: The input becomes enabled after the async transition.
    - expect: The entered value remains in the input.

#### 2.3. TC_006 - Disable an enabled input

**File:** `tests/the-internet/dynamic-controls.spec.ts`

**Steps:**
  1. Open /dynamic_controls, activate Enable and wait until enabled, then activate Disable.
    - expect: The input becomes disabled after the second async transition.
    - expect: The control label returns to Enable.

### 3. Disappearing Elements

**Seed:** `No seed file; browser exploration only.`

#### 3.1. TC_007 - Required navigation links render

**File:** `tests/the-internet/disappearing-elements.spec.ts`

**Steps:**
  1. Open /disappearing_elements and inspect the navigation list, allowing the optional Gallery entry to be present or absent.
    - expect: Home, About, Contact Us, and Portfolio links are visible.
    - expect: If Gallery is present, its link target is /gallery/; do not require its presence.

#### 3.2. TC_008 - Home navigation returns to the index

**File:** `tests/the-internet/disappearing-elements.spec.ts`

**Steps:**
  1. Open /disappearing_elements and activate the Home link.
    - expect: The browser navigates to the application root.
    - expect: The root heading Welcome to the-internet is visible.

#### 3.3. TC_009 - Reload retains required links despite optional entry variation

**File:** `tests/the-internet/disappearing-elements.spec.ts`

**Steps:**
  1. Open /disappearing_elements, reload once, and inspect the navigation list after each completed load.
    - expect: Home, About, Contact Us, and Portfolio remain available on the loaded page.
    - expect: Gallery may vary between loads and is not treated as a failure.

### 4. Challenging DOM

**Seed:** `No seed file; browser exploration only.`

#### 4.1. TC_010 - Table exposes expected columns and ten data rows

**File:** `tests/the-internet/challenging-dom.spec.ts`

**Steps:**
  1. Open /challenging_dom and inspect the data table.
    - expect: Headers Lorem, Ipsum, Dolor, Sit, Amet, Diceret, and Action are present.
    - expect: Ten data rows are rendered; row values may vary and should not be hard-coded.

#### 4.2. TC_011 - Edit action targets its row without removing table data

**File:** `tests/the-internet/challenging-dom.spec.ts`

**Steps:**
  1. On /challenging_dom, scope an Edit link to one data row and activate it.
    - expect: The link navigation target is #edit.
    - expect: The table remains rendered with ten data rows.

#### 4.3. TC_012 - Delete action link target is row-scoped

**File:** `tests/the-internet/challenging-dom.spec.ts`

**Steps:**
  1. On /challenging_dom, scope a Delete link to a selected data row and activate it.
    - expect: The link navigation target is #delete.
    - expect: The page and table remain available; do not assume the demo persists a row deletion.

### 5. Form Authentication

**Seed:** `No seed file; browser exploration only.`

#### 5.1. TC_013 - Valid credentials open the secure area

**File:** `tests/the-internet/form-authentication.spec.ts`

**Steps:**
  1. Open /login, enter tomsmith and SuperSecretPassword!, and submit the login form.
    - expect: The URL becomes /secure.
    - expect: A secure-area success message and Logout control are visible.

#### 5.2. TC_014 - Invalid username is rejected

**File:** `tests/the-internet/form-authentication.spec.ts`

**Steps:**
  1. Open /login, enter wrong_user with a non-empty password, and submit.
    - expect: The login page remains displayed.
    - expect: The error notification reads Your username is invalid!

#### 5.3. TC_015 - Invalid password is rejected

**File:** `tests/the-internet/form-authentication.spec.ts`

**Steps:**
  1. Open /login, enter tomsmith with an incorrect password, and submit.
    - expect: The login page remains displayed.
    - expect: The error notification reads Your password is invalid!

### 6. Dynamic Content

**Seed:** `No seed file; browser exploration only.`

#### 6.1. TC_016 - Dynamic content renders three text entries

**File:** `tests/the-internet/dynamic-content.spec.ts`

**Steps:**
  1. Open /dynamic_content and inspect the content entries after the page is ready.
    - expect: Three text entries are present and non-empty.
    - expect: Do not assert generated paragraph text against hard-coded copy.

#### 6.2. TC_017 - Content changes after refresh

**File:** `tests/the-internet/dynamic-content.spec.ts`

**Steps:**
  1. Open /dynamic_content, record the three entry texts, reload the page, then compare the refreshed texts.
    - expect: Three entries remain present after reload.
    - expect: The observed dynamic text differs after refresh; treat randomized content variation as expected but diagnostic if it does not change.

#### 6.3. TC_018 - Static-content query mode opens

**File:** `tests/the-internet/dynamic-content.spec.ts`

**Steps:**
  1. From /dynamic_content, activate the documented click here link for static content.
    - expect: The URL includes ?with_content=static.
    - expect: The Dynamic Content heading and three text entries are visible.

### 7. Add/Remove Elements

**Seed:** `No seed file; browser exploration only.`

#### 7.1. TC_019 - Add Element creates a Delete control

**File:** `tests/the-internet/add-remove-elements.spec.ts`

**Steps:**
  1. Open /add_remove_elements/ and activate Add Element once.
    - expect: One Delete button appears.

#### 7.2. TC_020 - Multiple added elements have independent Delete controls

**File:** `tests/the-internet/add-remove-elements.spec.ts`

**Steps:**
  1. Open /add_remove_elements/, activate Add Element three times, and inspect the controls.
    - expect: Exactly three Delete buttons are present.

#### 7.3. TC_021 - Delete removes one added control

**File:** `tests/the-internet/add-remove-elements.spec.ts`

**Steps:**
  1. Open /add_remove_elements/, add two elements, then activate one Delete button.
    - expect: One Delete button remains and the other is removed.

### 8. JavaScript Alerts

**Seed:** `No seed file; browser exploration only.`

#### 8.1. TC_022 - Accept JavaScript alert

**File:** `tests/the-internet/javascript-alerts.spec.ts`

**Steps:**
  1. Open /javascript_alerts, activate Click for JS Alert, verify the dialog message, and accept it.
    - expect: The dialog says I am a JS Alert.
    - expect: The page result reads You successfully clicked an alert.

#### 8.2. TC_023 - Cancel JavaScript confirmation

**File:** `tests/the-internet/javascript-alerts.spec.ts`

**Steps:**
  1. Open /javascript_alerts, activate Click for JS Confirm, and dismiss the dialog.
    - expect: The dialog says I am a JS Confirm.
    - expect: The page result reads You clicked: Cancel.

#### 8.3. TC_024 - Submit text through JavaScript prompt

**File:** `tests/the-internet/javascript-alerts.spec.ts`

**Steps:**
  1. Open /javascript_alerts, activate Click for JS Prompt, enter QA prompt value, and accept the dialog.
    - expect: The dialog says I am a JS prompt.
    - expect: The page result reads You entered: QA prompt value.

### 9. Status Codes

**Seed:** `No seed file; browser exploration only.`

#### 9.1. TC_025 - Status Codes 200 endpoint responds successfully

**File:** `tests/the-internet/status-codes.spec.ts`

**Steps:**
  1. Open /status_codes/200 and inspect the navigation response and page message.
    - expect: The navigation response status is 200.
    - expect: The page states it returned a 200 status code and provides a link back to /status_codes.

#### 9.2. TC_026 - Status Codes 301 endpoint returns its status response

**File:** `tests/the-internet/status-codes.spec.ts`

**Steps:**
  1. Open /status_codes/301 and inspect the response and page content.
    - expect: The navigation response status is 301.
    - expect: The page states it returned a 301 status code and provides a link back to /status_codes.

#### 9.3. TC_027 - Status Codes 404 endpoint shows not-found response

**File:** `tests/the-internet/status-codes.spec.ts`

**Steps:**
  1. Open /status_codes/404 and inspect the navigation response and page message.
    - expect: The navigation response status is 404.
    - expect: The page states it returned a 404 status code and provides a link back to /status_codes.

### 10. Multiple Windows

**Seed:** `No seed file; browser exploration only.`

#### 10.1. TC_028 - Click Here opens a new window

**File:** `tests/the-internet/multiple-windows.spec.ts`

**Steps:**
  1. Open /windows and activate Click Here while observing the browser context for a new page.
    - expect: A separate page opens at /windows/new.
    - expect: The new page shows the heading New Window.

#### 10.2. TC_029 - Parent remains on the opening page after popup opens

**File:** `tests/the-internet/multiple-windows.spec.ts`

**Steps:**
  1. Open /windows, activate Click Here, and inspect both pages.
    - expect: The child page shows New Window.
    - expect: The original page remains at /windows with its Opening a new window heading.

#### 10.3. TC_030 - New Window route is directly accessible

**File:** `tests/the-internet/multiple-windows.spec.ts`

**Steps:**
  1. Navigate directly to /windows/new in a fresh context.
    - expect: The page heading is New Window.
    - expect: The page remains on the /windows/new route.
