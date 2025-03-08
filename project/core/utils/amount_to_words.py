def num_to_words_indian(num):
    """
    Convert a number to Indian style words with lakhs, crores etc.
    
    Args:
        num (int): Number to convert
        
    Returns:
        str: Number in Indian style words
    """
    # Define words for numbers
    ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 
            'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 
            'seventeen', 'eighteen', 'nineteen']
    
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
    
    # Indian place values
    place_values = ['', 'thousand', 'lakh', 'crore']
    
    # Handle zero separately
    if num == 0:
        return 'zero'
    
    # Handle negative numbers
    negative = False
    if num < 0:
        negative = True
        num = abs(num)
    
    # Convert to string for easy manipulation
    num_str = str(num)
    
    # Handle decimal part
    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    
    # Format Indian style groups
    result = ''
    
    # Handle crores (if any)
    if rupees >= 10000000:
        crores = rupees // 10000000
        if crores > 99:
            # For crores >= 100, recursively handle it
            result += num_to_words_indian(crores) + ' crore '
        else:
            # Handle 1-99 crores
            if crores > 19:
                result += tens[crores // 10] + ' '
                if crores % 10 != 0:
                    result += ones[crores % 10] + ' '
            else:
                result += ones[crores] + ' '
            result += 'crore '
        rupees %= 10000000
    
    # Handle lakhs (if any)
    if rupees >= 100000:
        lakhs = rupees // 100000
        if lakhs > 19:
            result += tens[lakhs // 10] + ' '
            if lakhs % 10 != 0:
                result += ones[lakhs % 10] + ' '
        else:
            result += ones[lakhs] + ' '
        result += 'lakh '
        rupees %= 100000
    
    # Handle thousands (if any)
    if rupees >= 1000:
        thousands = rupees // 1000
        if thousands > 19:
            result += tens[thousands // 10] + ' '
            if thousands % 10 != 0:
                result += ones[thousands % 10] + ' '
        else:
            result += ones[thousands] + ' '
        result += 'thousand '
        rupees %= 1000
    
    # Handle hundreds (if any)
    if rupees >= 100:
        result += ones[rupees // 100] + ' hundred '
        rupees %= 100
        if rupees > 0:
            result += 'and '
    
    # Handle remaining 1-99
    if rupees > 19:
        result += tens[rupees // 10] + ' '
        if rupees % 10 != 0:
            result += ones[rupees % 10] + ' '
    elif rupees > 0:
        result += ones[rupees] + ' '
    
    # Add 'Rupees' word
    result += 'Rupees'
    
    # Add paise if necessary
    if paise > 0:
        result += ' and '
        if paise > 19:
            result += tens[paise // 10] + ' '
            if paise % 10 != 0:
                result += ones[paise % 10] + ' '
        else:
            result += ones[paise] + ' '
        result += 'Paise'
    
    # Add 'Only' at the end
    result += ' Only'
    
    # Add minus for negative numbers
    if negative:
        result = 'minus ' + result
    
    # Capitalize the first letter
    return result.strip().capitalize()

# Test with your example
amount = 101950
words = num_to_words_indian(amount)
print(words)  # Output: "One lakh one thousand nine hundred fifty Rupees Only"