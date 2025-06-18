import ollama
from typing import Dict, List, Any
import uuid
import json


class PIIDetector:
    def __init__(self):
        self.ollama = ollama
        # Storage for PII mappings: {session_id: {placeholder: original_value}}
        self.pii_mappings = {}
    
    def detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in the given text using Ollama.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing detection results
        """
        # Use Ollama for PII detection
        ollama_findings = self._check_with_ollama(text)
        
        return {
            'has_pii': ollama_findings['has_pii'],
            'types': ollama_findings['types'],
            'confidence': ollama_findings.get('confidence', 'low'),
            'text': text
        }
    
    def _check_with_ollama(self, text: str) -> Dict[str, Any]:
        """Use Ollama to detect PII."""
        prompt = f"""
        Analyze the following text and identify any Personally Identifiable Information (PII):
        
        Text: "{text}"
        
        Look for:
        - Names (first names, last names, full names)
        - Social Security Numbers
        - Email addresses
        - Phone numbers
        - Credit card numbers
        - Addresses
        - Dates of birth
        - Driver's license numbers
        - Passport numbers
        - Any other personal identifiers
        
        Respond with a JSON object in this format:
        {{
            "has_pii": true/false,
            "types": ["type1", "type2"],
            "confidence": "high/medium/low"
        }}
        
        Only respond with the JSON object, no additional text.
        """
        
        try:
            response = self.ollama.chat(
                model="llama3.1",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Try to parse the response as JSON
            import json
            try:
                result = json.loads(response.message.content.strip())
                return {
                    'has_pii': result.get('has_pii', False),
                    'types': result.get('types', []),
                    'confidence': result.get('confidence', 'low')
                }
            except json.JSONDecodeError:
                # Fallback: check if response contains PII indicators
                pii_indicators = ['true', 'yes', 'found', 'detected']
                has_pii = any(indicator in response.message.content.lower() for indicator in pii_indicators)
                return {
                    'has_pii': has_pii,
                    'types': ['unknown'] if has_pii else [],
                    'confidence': 'low'
                }
                
        except Exception as e:
            # Return no PII detected on error
            return {
                'has_pii': False,
                'types': [],
                'confidence': 'low',
                'error': str(e)
            }
    
    def is_sensitive(self, text: str) -> bool:
        """
        Simple method to check if text contains sensitive information.
        
        Args:
            text: Input text to check
            
        Returns:
            True if sensitive information is detected, False otherwise
        """
        result = self.detect_pii(text)
        return result['has_pii']
    
    def get_pii_types(self, text: str) -> List[str]:
        """
        Get the types of PII detected in the text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected PII types
        """
        result = self.detect_pii(text)
        return result['types']
    
    def mask(self, text: str, session_id: str = None) -> Dict[str, Any]:
        """
        Mask PII in the given text with placeholder values and record mappings.
        
        Args:
            text: Input text to mask
            session_id: Optional session ID for mapping storage. If None, generates one.
            
        Returns:
            Dictionary containing masked text, session_id, and mapping info
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        prompt = f"""
        Analyze the following text and extract ALL specific PII values that need to be masked. Be thorough and identify every piece of personal information:
        
        Text: "{text}"
        
        Extract EXACT values for:
        - Names (first names, last names, full names) - extract the complete name as it appears
        - Social Security Numbers - exact format as shown
        - Email addresses - complete email address
        - Phone numbers - exact format as shown
        - Credit card numbers - exact format as shown
        - Street addresses - complete address
        - Dates of birth - exact format as shown
        - Driver's license numbers - exact format as shown
        - Passport numbers - exact format as shown
        - Any other personal identifiers
        
        For the text "{text}", identify EVERY PII value and respond with a JSON object:
        {{
            "pii_items": [
                {{"value": "John Doe", "type": "name"}},
                {{"value": "123-45-6789", "type": "ssn"}},
                {{"value": "john.doe@example.com", "type": "email"}},
                ...
            ]
        }}
        
        Be very thorough - extract ALL personal information found. Use the exact text as it appears.
        Only respond with the JSON object, no additional text.
        """
        
        try:
            response = self.ollama.chat(
                model="llama3.1",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse PII items from response
            try:
                result = json.loads(response.message.content.strip())
                pii_items = result.get('pii_items', [])
            except json.JSONDecodeError:
                # If JSON parsing fails, try a more robust approach
                pii_items = self._fallback_pii_extraction(text)
            
            # Initialize session mapping if it doesn't exist
            if session_id not in self.pii_mappings:
                self.pii_mappings[session_id] = {}
            
            masked_text = text
            placeholder_map = {}
            
            # Create placeholders and replace PII
            for item in pii_items:
                pii_value = item.get('value', '').strip()
                pii_type = item.get('type', 'other').lower()
                
                if pii_value and pii_value in text:
                    # Generate unique placeholder
                    placeholder_id = str(uuid.uuid4())[:8]
                    placeholder = f"[{pii_type.upper()}_{placeholder_id}]"
                    
                    # Store mapping
                    self.pii_mappings[session_id][placeholder] = pii_value
                    placeholder_map[pii_value] = placeholder
                    
                    # Replace in text
                    masked_text = masked_text.replace(pii_value, placeholder)
            
            return {
                'masked_text': masked_text,
                'session_id': session_id,
                'mappings_count': len(placeholder_map),
                'placeholder_map': placeholder_map
            }
            
        except Exception as e:
            # Fallback: return original text if masking fails
            return {
                'masked_text': text,
                'session_id': session_id,
                'mappings_count': 0,
                'placeholder_map': {},
                'error': str(e)
            }
    
    def _fallback_pii_extraction(self, text: str) -> List[Dict[str, str]]:
        """
        Fallback method to extract PII when JSON parsing fails.
        Uses a simpler LLM prompt to identify PII.
        """
        prompt = f"""
        List all personal information in this text: "{text}"
        
        Format each item as: TYPE: VALUE
        
        Examples:
        NAME: John Doe
        SSN: 123-45-6789
        EMAIL: john.doe@example.com
        """
        
        try:
            response = self.ollama.chat(
                model="llama3.1",
                messages=[{"role": "user", "content": prompt}]
            )
            
            pii_items = []
            lines = response.message.content.strip().split('\n')
            
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        pii_type = parts[0].strip().lower()
                        pii_value = parts[1].strip()
                        if pii_value and pii_value in text:
                            pii_items.append({
                                'value': pii_value,
                                'type': pii_type
                            })
            
            return pii_items
            
        except Exception:
            return []
    
    def unmask(self, masked_text: str, session_id: str) -> str:
        """
        Restore original PII values from masked text using stored mappings.
        
        Args:
            masked_text: Text with PII placeholders
            session_id: Session ID to retrieve mappings
            
        Returns:
            Text with original PII values restored
        """
        if session_id not in self.pii_mappings:
            return masked_text
        
        unmasked_text = masked_text
        mappings = self.pii_mappings[session_id]
        
        # Replace placeholders with original values
        for placeholder, original_value in mappings.items():
            unmasked_text = unmasked_text.replace(placeholder, original_value)
        
        return unmasked_text
    
    def get_session_mappings(self, session_id: str) -> Dict[str, str]:
        """
        Get all PII mappings for a specific session.
        
        Args:
            session_id: Session ID to retrieve mappings for
            
        Returns:
            Dictionary of placeholder to original value mappings
        """
        return self.pii_mappings.get(session_id, {})
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear PII mappings for a specific session.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            True if session was cleared, False if session didn't exist
        """
        if session_id in self.pii_mappings:
            del self.pii_mappings[session_id]
            return True
        return False


if __name__ == "__main__":
    detector = PIIDetector()
    text = "Hi I am John Doe. My SSN is 123-45-6789 and my email is john.doe@example.com"
    print("Original text:", text)
    print('--------------------------------')
    print(detector.detect_pii(text))
    print('--------------------------------')
    print("Is sensitive:", detector.is_sensitive(text))
    print('--------------------------------')
    print("PII types:", detector.get_pii_types(text))
    print('--------------------------------')
    
    # Test masking with session management
    mask_result = detector.mask(text)
    session_id = mask_result['session_id']
    masked_text = mask_result['masked_text']
    
    print("Masked text:", masked_text)
    print("Session ID:", session_id)
    print("Mappings count:", mask_result['mappings_count'])
    print('--------------------------------')
    
    # Test unmasking
    unmasked_text = detector.unmask(masked_text, session_id)
    print("Unmasked text:", unmasked_text)
    print('--------------------------------')
    
    # Show session mappings
    mappings = detector.get_session_mappings(session_id)
    print("Session mappings:", mappings)
    print('--------------------------------')
    
    # Test with a response that might contain the masked text
    simulated_response = f"Thank you for your message: {masked_text}. We will contact you soon."
    print("Simulated response with masked text:", simulated_response)
    restored_response = detector.unmask(simulated_response, session_id)
    print("Restored response:", restored_response)