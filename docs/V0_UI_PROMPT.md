# 🎨 V0 UI Prompt for RAG Chat Application

## **Context & Requirements**

Create a modern, interactive chat interface for a RAG (Retrieval-Augmented Generation) application. This is a conversational AI system that helps users ask questions and get intelligent responses based on a knowledge base.

## **Design Requirements**

### **Overall Theme & Style**
- **Modern & Clean**: Minimalist design with plenty of white space
- **Professional**: Suitable for business/enterprise use
- **Accessible**: High contrast, readable fonts, keyboard navigation
- **Responsive**: Works perfectly on desktop, tablet, and mobile
- **Color Scheme**: 
  - Primary: Blue (#3B82F6, #2563EB)
  - Secondary: Gray (#6B7280, #9CA3AF)
  - Background: Light gray (#F9FAFB, #F3F4F6)
  - Success: Green (#10B981)
  - Error: Red (#EF4444)

### **Layout Structure**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header (Logo + Navigation)                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │                         │  │                                         │  │
│  │  Sidebar                │  │  Chat Messages Area (Scrollable)        │  │
│  │  • Product Showcase     │  │  • User messages (right-aligned, blue)  │  │
│  │  • Product Cards        │  │  • AI responses (left-aligned, white)   │  │
│  │  • Product Details      │  │  • Loading indicators                   │  │
│  │  • Search Products      │  │  • Typing animations                    │  │
│  │  • Filter Options       │  │  • Product recommendations             │  │
│  │  • Categories           │  │                                         │  │
│  │                         │  │                                         │  │
│  │  Collapsible/Expandable │  │                                         │  │
│  │  (Mobile: Hidden)       │  │                                         │  │
│  └─────────────────────────┘  └─────────────────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input Area (Fixed at bottom)                                               │
│ • Text input with placeholder                                              │
│ • Send button with hover effects                                           │
│ • Voice input option (optional)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## **Key Components**

### **1. Header Section**
- **Logo**: Clean, modern logo with app name "RAG Chat"
- **Navigation**: Simple menu with "Chat", "History", "Settings"
- **User Avatar**: Circular profile picture in top-right
- **Status Indicator**: Online/offline status with colored dot
- **Sidebar Toggle**: Hamburger menu for mobile, collapse/expand for desktop

### **2. Sidebar Section**
- **Product Showcase**:
  - Product cards with images, titles, prices
  - Hover effects with quick preview
  - Click to view detailed product information
  - "Add to cart" or "View details" buttons
- **Product Search**:
  - Search bar with autocomplete
  - Filter by category, price, rating
  - Sort options (price, popularity, rating)
- **Categories**:
  - Collapsible category tree
  - Category icons and counts
  - Quick filter buttons
- **Product Details Panel**:
  - Detailed product information
  - Image gallery with thumbnails
  - Specifications and features
  - Related products section
- **Responsive Behavior**:
  - Desktop: Always visible sidebar
  - Tablet: Collapsible sidebar
  - Mobile: Hidden by default, slide-in overlay

### **3. Chat Messages Area**
- **Message Bubbles**:
  - User messages: Blue background, right-aligned, rounded corners
  - AI messages: White background, left-aligned, subtle shadow
  - Typing indicators: Animated dots when AI is responding
  - Product recommendations: Special styled cards within messages
- **Message Metadata**:
  - Timestamp (small, gray text)
  - Read receipts (for user messages)
  - Source citations (for AI responses)
  - Product references with links to sidebar
- **Product Integration**:
  - AI can reference products from sidebar
  - Click on product mentions to view in sidebar
  - Product cards embedded in chat responses
- **Animations**:
  - Messages slide in from bottom with fade effect
  - Smooth scrolling to new messages
  - Hover effects on message bubbles
  - Product cards slide in with staggered animation

### **4. Input Area**
- **Text Input**:
  - Large, comfortable input field
  - Placeholder: "Ask me anything about our knowledge base..."
  - Auto-resize based on content
  - Character counter (optional)
- **Send Button**:
  - Circular button with send icon
  - Hover animation (scale up)
  - Loading state when sending
- **Additional Features**:
  - File attachment button
  - Voice input button
  - Emoji picker (optional)

### **5. Interactive Elements**

#### **Message Interactions**
- **Hover Effects**: Subtle background change on message hover
- **Click Actions**: 
  - Copy message text
  - React with emoji
  - Flag for review
- **Long Press**: Context menu with options

#### **Loading States**
- **Typing Indicator**: Three animated dots
- **Skeleton Loading**: Placeholder content while loading
- **Progress Bar**: For long operations

#### **Animations & Transitions**
- **Page Load**: Fade in from top
- **Message Send**: Slide up from input
- **Message Receive**: Slide in from left
- **Button Hover**: Scale and color transitions
- **Loading**: Smooth pulse animations

## **User Experience Features**

### **1. Accessibility**
- **Keyboard Navigation**: Tab through all interactive elements
- **Screen Reader**: Proper ARIA labels and descriptions
- **High Contrast**: Meets WCAG guidelines
- **Focus Indicators**: Clear focus states for all elements

### **2. Responsive Design**
- **Mobile**: Stacked layout, touch-friendly buttons, sidebar as overlay
- **Tablet**: Side-by-side layout when space allows, collapsible sidebar
- **Desktop**: Full-width layout with optimal spacing, always-visible sidebar

### **3. Performance**
- **Lazy Loading**: Load messages as needed
- **Smooth Scrolling**: 60fps animations
- **Optimized Images**: WebP format, proper sizing
- **Caching**: Efficient state management

## **Visual Design Details**

### **Typography**
- **Primary Font**: Inter or SF Pro Display
- **Secondary Font**: System font stack
- **Sizes**: 
  - Headers: 24px, 20px, 18px
  - Body: 16px, 14px
  - Captions: 12px

### **Spacing & Layout**
- **Grid System**: 8px base unit
- **Margins**: 16px, 24px, 32px
- **Padding**: 12px, 16px, 20px
- **Border Radius**: 8px, 12px, 16px

### **Shadows & Depth**
- **Message Bubbles**: Subtle shadow (0 2px 8px rgba(0,0,0,0.1))
- **Cards**: Medium shadow (0 4px 12px rgba(0,0,0,0.15))
- **Modals**: Heavy shadow (0 8px 24px rgba(0,0,0,0.2))

### **Micro-interactions**
- **Button Press**: Scale down effect
- **Input Focus**: Border color change
- **Message Hover**: Slight lift effect
- **Loading**: Smooth pulse animation

## **Advanced Features**

### **1. Message Types**
- **Text Messages**: Standard chat bubbles
- **Rich Content**: Support for markdown, links, images
- **Product Messages**: Special styled product recommendation cards
- **System Messages**: Notifications, errors, warnings
- **Typing Indicators**: Animated dots

### **2. Search & History**
- **Search Bar**: Filter through conversation history
- **Product Search**: Search products in sidebar
- **Date Groups**: Group messages by date
- **Quick Actions**: Pin important messages
- **Product Filtering**: Filter products by category, price, rating

### **3. Settings & Customization**
- **Theme Toggle**: Light/dark mode
- **Font Size**: Adjustable text size
- **Sound Toggle**: Enable/disable notification sounds

## **Animation Specifications**

### **1. Entrance Animations**
```css
/* Message slide in */
@keyframes slideIn {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Page load */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### **2. Interactive Animations**
```css
/* Button hover */
@keyframes scaleUp {
  from { transform: scale(1); }
  to { transform: scale(1.05); }
}

/* Typing indicator */
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
```

## **Error States & Feedback**

### **1. Error Messages**
- **Network Errors**: Clear error message with retry option
- **Validation Errors**: Inline validation with helpful text
- **Loading Errors**: Graceful fallback with retry button

### **2. Success States**
- **Message Sent**: Brief confirmation animation
- **Connection Restored**: Subtle notification
- **Settings Saved**: Success toast message

## **Mobile-Specific Considerations**

### **1. Touch Interactions**
- **Tap Targets**: Minimum 44px for all interactive elements
- **Swipe Actions**: Swipe to delete/reply to messages
- **Pull to Refresh**: Refresh conversation history

### **2. Mobile Layout**
- **Bottom Navigation**: Fixed navigation at bottom
- **Floating Action Button**: Quick access to new chat
- **Keyboard Handling**: Adjust layout when keyboard appears

## **Performance Requirements**

### **1. Loading Times**
- **Initial Load**: < 2 seconds
- **Message Send**: < 500ms feedback
- **Message Receive**: < 100ms display

### **2. Smooth Interactions**
- **60fps Animations**: All animations should be smooth
- **No Layout Shift**: Prevent content jumping
- **Efficient Rendering**: Virtual scrolling for long conversations

## **Final Notes**

- **Focus on UX**: Every interaction should feel natural and intuitive
- **Consistent Design**: Maintain design system throughout
- **Accessibility First**: Ensure the interface works for everyone
- **Performance**: Optimize for speed and smoothness
- **Modern Standards**: Use latest web technologies and best practices

Create a beautiful, functional chat interface that users will love to interact with. The design should feel modern, professional, and highly responsive to user interactions. 