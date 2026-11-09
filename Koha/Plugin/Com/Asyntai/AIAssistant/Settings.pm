package Koha::Plugin::Com::Asyntai::AIAssistant::Settings;

# Everything the plugin decides about a stored value. It touches nothing outside
# itself, so the tests run it without Koha.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

use Modern::Perl;

use constant DEFAULT_SCRIPT_URL => 'https://widget.asyntai.com/static/js/chat-widget.js';
use constant GUIDE_URL          => 'https://asyntai.com/documentation/integrations/koha/';

# Reads a widget ID out of a stored value. Accepts a bare ID or the whole snippet
# from the Asyntai dashboard, because administrators paste the snippet. Answers an
# empty string when there is nothing usable, which keeps the chat switched off.
sub read_widget_id {
    my ( $class, $raw ) = @_;

    my $value = _trim($raw);

    # A pasted snippet can arrive HTML encoded, so decode the quotes first.
    $value =~ s/&quot;|&\#0*34;|&\#x0*22;/"/gxmsi;
    $value =~ s/&apos;|&\#0*39;|&\#x0*27;/'/gxmsi;

    if ( $value =~ /data-asyntai-id\s*=\s*["']([^"']+)["']/xms ) {
        $value = _trim($1);
    }

    return $value =~ /\Aasyntai_[[:alnum:]]{6,64}\z/xms ? $value : q{};
}

# Reads the script address out of a stored value. Only an https address is
# accepted, so a bad value can never put a javascript: address on every page. An
# empty field means the Asyntai address. A bad value answers an empty string.
sub read_script_url {
    my ( $class, $raw ) = @_;

    my $value = _trim($raw);

    return DEFAULT_SCRIPT_URL if $value eq q{};

    return $value =~ m{\Ahttps://[^\s"'<>]+\z}xmsi ? $value : q{};
}

# Writes the script element, the same element as the dashboard snippet. It is not
# inline code, so it also works under a content security policy that allows the host.
sub loader_tag {
    my ( $class, $widget_id, $script_url, $nonce ) = @_;

    my $nonce_attribute = $nonce ? sprintf ' nonce="%s"', _escape($nonce) : q{};

    return sprintf '<script async src="%s" data-asyntai-id="%s"%s></script>',
        _escape($script_url), _escape($widget_id), $nonce_attribute;
}

sub _trim {
    my ($value) = @_;

    return ( $value // q{} ) =~ s/\A\s+|\s+\z//gxmsr;
}

sub _escape {
    my ($value) = @_;

    $value =~ s/&/&amp;/gxms;
    $value =~ s/"/&quot;/gxms;
    $value =~ s/</&lt;/gxms;
    $value =~ s/>/&gt;/gxms;

    return $value;
}

1;
