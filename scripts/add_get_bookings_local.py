#!/usr/bin/env python3
"""Add get_bookings method to lead_manager.py"""

# Read the file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\handlers\tools\lead_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Method to add
new_method = '''
    def get_bookings(self, customer_phone: str) -> Dict[str, Any]:
        """
        Search for bookings by phone number with caching

        Args:
            customer_phone: Customer's phone number to search

        Returns:
            dict: {
                'success': bool,
                'bookings': list of matching booking dicts,
                'count': int
            }
        """
        logger.info("="*80)
        logger.info(f"🔍 SEARCHING BOOKINGS FOR: {customer_phone}")
        logger.info("="*80)

        if not self.bookings_sheet:
            logger.error("❌ Bookings sheet not initialized")
            return {
                'success': False,
                'bookings': [],
                'count': 0,
                'message': 'Bookings sheet not available'
            }

        try:
            # Check cache first
            cache_key = 'all_bookings'
            all_bookings = self.cache_manager.get(cache_key)

            if all_bookings is None:
                # Cache miss - fetch from sheets
                logger.info("📥 Cache miss - fetching from Google Sheets...")
                all_bookings = self.bookings_sheet.get_all_records()
                self.cache_manager.set(cache_key, all_bookings)
                logger.info(f"✓ Cached {len(all_bookings)} bookings (TTL: 300s)")
            else:
                logger.info(f"✓ Cache hit - using cached data ({len(all_bookings)} bookings)")

            # Search for matching phone number
            # Normalize phone for comparison (remove spaces, dashes, etc)
            normalized_search = ''.join(filter(str.isdigit, customer_phone))

            matching_bookings = []
            for booking in all_bookings:
                booking_phone = str(booking.get('Phone', ''))
                normalized_booking_phone = ''.join(filter(str.isdigit, booking_phone))

                if normalized_search in normalized_booking_phone or normalized_booking_phone in normalized_search:
                    matching_bookings.append(booking)

            logger.info(f"✅ Found {len(matching_bookings)} matching booking(s)")
            logger.info("="*80)

            return {
                'success': True,
                'bookings': matching_bookings,
                'count': len(matching_bookings),
                'message': f'Found {len(matching_bookings)} booking(s)'
            }

        except Exception as e:
            logger.error(f"❌ Failed to search bookings: {str(e)}")
            logger.exception("Full error traceback:")
            logger.info("="*80)
            return {
                'success': False,
                'bookings': [],
                'count': 0,
                'message': f'Error searching bookings: {str(e)}'
            }
'''

# Add the method at the end of the file
content = content + new_method

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\handlers\tools\lead_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] get_bookings() method added to lead_manager.py')
