    def send_voice(self, to: str, voice_url: str) -> Dict[str, Any]:
        """
        Send a voice message via WhatsApp using Whapi API
        
        Voice messages appear as voice notes in WhatsApp (not as document files).
        The audio file should be in OGG format with Opus codec for best compatibility.

        Args:
            to (str): Recipient phone number
            voice_url (str): URL of the voice/audio file to send (preferably OGG/Opus)

        Returns:
            dict: {'success': bool, 'error': str or None, 'message_id': str or None}
        """
        logger.info("="*60)
        logger.info("SENDING WHATSAPP VOICE MESSAGE")
        logger.info("="*60)

        logger.debug(f"To (raw): {to}")
        logger.debug(f"Voice URL: {voice_url}")

        # Format phone number for WHAPI (must include @s.whatsapp.net suffix)
        formatted_to = self.format_phone_number(to)
        logger.debug(f"To (formatted): {formatted_to}")

        url = f"{self.base_url}/messages/voice"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'to': formatted_to,
            'media': voice_url
        }

        try:
            logger.debug(f"Calling Whapi API: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            message_id = response_data.get('id', None)

            logger.info("✓ Voice message sent successfully")
            logger.info(f"  Message ID: {message_id}")
            logger.info("="*60)

            return {
                'success': True,
                'error': None,
                'message_id': message_id,
                'data': response_data
            }

        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            response_text = http_err.response.text if http_err.response else ''

            if status_code == 401:
                error_msg = "Unauthorized: check WHAPI_API_TOKEN"
            elif status_code == 402:
                error_msg = "Payment required: please check Whapi plan or balance"
            elif status_code == 403:
                error_msg = "Forbidden: check Whapi channel permissions or region"
            elif status_code == 429:
                error_msg = "Too many requests: Whapi rate limit reached, retry later"
            else:
                error_msg = f"HTTP {status_code}: {response_text}" if status_code else str(http_err)

            logger.error("❌ Failed to send WhatsApp voice message")
            logger.error(f"HTTPError: {error_msg}")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'success': False,
                'error': error_msg,
                'message_id': None
            }

        except Exception as e:
            logger.error("❌ Failed to send WhatsApp voice message")
            logger.error(f"Error: {str(e)}")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'success': False,
                'error': str(e),
                'message_id': None
            }

