package Koha::Plugin::Com::Asyntai::AIAssistant;

# Puts the Asyntai AI chat on the public catalog (OPAC) of Koha.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

use Modern::Perl;

use base qw(Koha::Plugins::Base);

use C4::Context;

use Koha::Plugin::Com::Asyntai::AIAssistant::Settings;

our $VERSION  = '1.0.1';
our $metadata = {
    name            => 'Asyntai AI Assistant',
    author          => 'Asyntai',
    date_authored   => '2026-11-07',
    date_updated    => '2026-11-07',
    minimum_version => '24.11.00.000',
    version         => $VERSION,
    license         => 'GPL-3.0',
    description     => 'Adds the Asyntai AI chat to your public catalog. It answers your patrons from your own library content.',
};

sub new {
    my ( $class, $args ) = @_;

    $args->{metadata} = $metadata;
    $args->{metadata}->{class} = $class;

    return $class->SUPER::new($args);
}

sub install {
    return 1;
}

sub upgrade {
    return 1;
}

sub uninstall {
    return 1;
}

# Until a library saves a widget ID the hook writes nothing, so an unfinished
# setup changes no page. The staff interface has no hook here and never gets the chat.
sub opac_js {
    my ($self) = @_;

    my $settings = 'Koha::Plugin::Com::Asyntai::AIAssistant::Settings';

    my $widget_id  = $settings->read_widget_id( $self->retrieve_data('widget_id') );
    my $script_url = $settings->read_script_url( $self->retrieve_data('script_url') );

    return q{} if $widget_id eq q{} || $script_url eq q{};

    if ( $self->retrieve_data('guests_only') ) {
        my $userenv = C4::Context->userenv;
        return q{} if $userenv && $userenv->{number};
    }

    return $settings->loader_tag( $widget_id, $script_url, _csp_nonce() );
}

sub configure {
    my ($self) = @_;

    my $cgi      = $self->{cgi};
    my $settings = 'Koha::Plugin::Com::Asyntai::AIAssistant::Settings';
    my $template = $self->get_template( { file => 'configure.tt' } );

    my %form;
    my $op = $cgi->param('op') // q{};

    if ( $op eq 'cud-save' ) {
        my $raw_id  = $cgi->param('widget_id')  // q{};
        my $raw_url = $cgi->param('script_url') // q{};

        my $widget_id = $settings->read_widget_id($raw_id);
        my $has_id    = $raw_id =~ /\S/xms;

        %form = (
            widget_id   => $raw_id,
            script_url  => $raw_url,
            guests_only => $cgi->param('guests_only') ? 1 : 0,
        );

        if ( $has_id && $widget_id eq q{} ) {
            $template->param( error_widget_id => 1 );
        } elsif ( $settings->read_script_url($raw_url) eq q{} ) {
            $template->param( error_script_url => 1 );
        } else {
            $self->store_data(
                {
                    widget_id   => $widget_id,
                    script_url  => $raw_url =~ s/^\s+|\s+$//gxmsr,
                    guests_only => $form{guests_only},
                }
            );
            $form{widget_id} = $widget_id;
            $template->param( saved => 1 );
        }
    } else {
        %form = (
            widget_id   => $self->retrieve_data('widget_id'),
            script_url  => $self->retrieve_data('script_url'),
            guests_only => $self->retrieve_data('guests_only'),
        );
    }

    $template->param(
        %form,
        default_script_url => $settings->DEFAULT_SCRIPT_URL,
        guide_url          => $settings->GUIDE_URL,
        class              => scalar $cgi->param('class'),
        method             => scalar $cgi->param('method'),
    );

    return $self->output_html( $template->output() );
}

# Koha has a nonce only when a library has switched on its content security
# policy, and older versions do not have this module.
sub _csp_nonce {
    return q{} unless eval { require Koha::ContentSecurityPolicy; 1 };

    my $csp = Koha::ContentSecurityPolicy->new;

    return $csp->is_enabled ? $csp->get_nonce // q{} : q{};
}

1;
